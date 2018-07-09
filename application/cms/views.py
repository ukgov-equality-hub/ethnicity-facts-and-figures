import json

from flask import (
    redirect,
    render_template,
    request,
    url_for,
    abort,
    flash,
    current_app,
    jsonify,
    session
)
from flask_login import login_required, current_user
from werkzeug.datastructures import CombinedMultiDict
from wtforms.validators import Optional

from application.auth.models import CREATE_MEASURE, CREATE_VERSION, DELETE_MEASURE, PUBLISH, UPDATE_MEASURE
from application.cms import cms_blueprint
from application.cms.categorisation_service import categorisation_service
from application.cms.data_utils import ChartObjectDataBuilder
from application.cms.dimension_service import dimension_service
from application.cms.exceptions import (
    PageNotFoundException,
    DimensionNotFoundException,
    DimensionAlreadyExists,
    PageExistsException,
    UploadNotFoundException,
    UpdateAlreadyExists,
    UploadCheckError,
    StaleUpdateException,
    UploadAlreadyExists,
    PageUnEditable
)
from application.cms.forms import (
    MeasurePageForm,
    DimensionForm,
    MeasurePageRequiredForm,
    DimensionRequiredForm,
    UploadForm,
    NewVersionForm
)
from application.cms.models import (
    publish_status,
    TypeOfData,
    FrequencyOfRelease,
    TypeOfStatistic,
    UKCountry,
    Organisation,
    LowestLevelOfGeography,
    Page
)
from application.cms.page_service import page_service
from application.cms.upload_service import upload_service
from application.sitebuilder import build_service
from application.sitebuilder.build_service import request_build
from application.utils import get_bool, user_can, user_has_access


@cms_blueprint.route('/')
@login_required
def index():
    return redirect(url_for('static_site.index'))


@cms_blueprint.route('/<topic>/<subtopic>/measure/new', methods=['GET', 'POST'])
@login_required
@user_can(CREATE_MEASURE)
def create_measure_page(topic, subtopic):
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
    except PageNotFoundException:
        abort(404)

    # Check the subtopic belongs to the topic
    if subtopic_page.parent != topic_page:
        abort(404)

    form = MeasurePageForm(frequency_choices=FrequencyOfRelease,
                           type_of_statistic_choices=TypeOfStatistic,
                           lowest_level_of_geography_choices=LowestLevelOfGeography)
    if form.validate_on_submit():
        try:
            # this subtopic stuff is a bit stupid but they insist in loading more nonsense into this form
            # the original design was move was a separate activity not bundled up with edit
            form_data = form.data
            form_data['subtopic'] = request.form.get('subtopic', None)

            # new measure does not have db_version_id pop it here as it seems like
            # WTForms will add one if not in page.
            form_data.pop('db_version_id', None)

            page = page_service.create_page(page_type='measure',
                                            parent=subtopic_page,
                                            data=form_data,
                                            created_by=current_user.email)

            message = 'Created page {}'.format(page.title)
            flash(message, 'info')
            current_app.logger.info(message)
            return redirect(url_for("cms.edit_measure_page",
                                    topic=topic_page.guid,
                                    subtopic=subtopic_page.guid,
                                    measure=page.guid,
                                    version=page.version))
        except PageExistsException as e:
            message = str(e)
            flash(message, 'error')
            current_app.logger.error(message)
            return redirect(url_for("cms.create_measure_page",
                                    form=form,
                                    topic=topic,
                                    subtopic=subtopic))

    ordered_topics = sorted(page_service.get_pages_by_type('topic'), key=lambda t: t.title)

    return render_template("cms/edit_measure_page.html",
                           form=form,
                           topic=topic_page,
                           subtopic=subtopic_page,
                           measure={},
                           new=True,
                           organisations_by_type=Organisation.select_options_by_type(),
                           topics=ordered_topics)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/uploads/<upload>/delete', methods=['GET'])
@login_required
@user_has_access
def delete_upload(topic, subtopic, measure, version, upload):

    *_, measure_page, upload_object = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version, upload=upload)

    upload_service.delete_upload_obj(measure_page, upload_object)

    message = 'Deleted upload {}'.format(upload_object.title)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/uploads/<upload>/edit', methods=['GET', 'POST'])
@login_required
@user_has_access
def edit_upload(topic, subtopic, measure, version, upload):

    topic_page, subtopic_page, measure_page, upload_object = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version, upload=upload)

    form = UploadForm(obj=upload_object)

    if request.method == 'POST':
        form = UploadForm(CombinedMultiDict((request.files, request.form)))
        if form.validate():
            f = form.upload.data if form.upload.data else None
            try:
                upload_service.edit_upload(measure=measure_page,
                                           upload=upload_object,
                                           file=f,
                                           data=form.data)
                message = 'Updated upload {}'.format(upload_object.title)
                flash(message, 'info')
                return redirect(url_for("cms.edit_measure_page",
                                        topic=topic,
                                        subtopic=subtopic,
                                        measure=measure,
                                        version=version))
            except UploadCheckError as e:
                message = 'Error uploading file. {}'.format(str(e))
                current_app.logger.exception(e)
                flash(message, 'error')

    context = {"form": form,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page,
               "upload": upload_object
               }
    return render_template("cms/edit_upload.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/delete', methods=['GET'])
@login_required
@user_has_access
def delete_dimension(topic, subtopic, measure, version, dimension):

    *_, measure_page, dimension_object = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version, dimension=dimension)

    dimension_service.delete_dimension(measure_page, dimension_object.guid)

    message = 'Deleted dimension {}'.format(dimension_object.title)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


def _diff_updates(form, page):
    from lxml.html.diff import htmldiff
    diffs = {}
    for k, v in form.data.items():
        if hasattr(page, k) and k != 'db_version_id':
            page_value = getattr(page, k)
            if v is not None and page_value is not None:
                diff = htmldiff(str(page_value).rstrip(), str(v).rstrip())
                if '<ins>' in diff or '<del>' in diff:
                    getattr(form, k).errors.append('has been updated by %s' % page.last_updated_by)
                    diffs[k] = diff
    form.db_version_id.data = page.db_version_id
    return diffs


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/edit', methods=['GET', 'POST'])
@login_required
@user_has_access
def edit_measure_page(topic, subtopic, measure, version):

    *_, measure_page = _get_measure_hierarchy_if_consistent_or_404(topic, subtopic, measure, version)
    topics = page_service.get_pages_by_type('topic')
    topics.sort(key=lambda page: page.title)
    diffs = {}

    if measure_page.type_of_data is not None:
        administrative_data = True if TypeOfData.ADMINISTRATIVE in measure_page.type_of_data else False
        survey_data = True if TypeOfData.SURVEY in measure_page.type_of_data else False
    else:
        administrative_data = survey_data = False

    if measure_page.secondary_source_1_type_of_data is not None:
        secondary_source_1_administrative_data = (
            True if TypeOfData.ADMINISTRATIVE in measure_page.secondary_source_1_type_of_data else False
        )
        secondary_source_1_survey_data = (
            True if TypeOfData.SURVEY in measure_page.secondary_source_1_type_of_data else False
        )
    else:
        secondary_source_1_administrative_data = secondary_source_1_survey_data = False

    if measure_page.area_covered is not None:
        if UKCountry.UK in measure_page.area_covered:
            england = wales = scotland = northern_ireland = True
        else:
            england = True if UKCountry.ENGLAND in measure_page.area_covered else False
            wales = True if UKCountry.WALES in measure_page.area_covered else False
            scotland = True if UKCountry.SCOTLAND in measure_page.area_covered else False
            northern_ireland = True if UKCountry.NORTHERN_IRELAND in measure_page.area_covered else False
    else:
        england = wales = scotland = northern_ireland = False

    form = MeasurePageForm(obj=measure_page,
                           administrative_data=administrative_data,
                           survey_data=survey_data,
                           secondary_source_1_administrative_data=secondary_source_1_administrative_data,
                           secondary_source_1_survey_data=secondary_source_1_survey_data,
                           frequency_choices=FrequencyOfRelease,
                           type_of_statistic_choices=TypeOfStatistic,
                           england=england,
                           wales=wales,
                           scotland=scotland,
                           northern_ireland=northern_ireland,
                           lowest_level_of_geography_choices=LowestLevelOfGeography)

    # Temporary to work out issue with data deletions
    if request.method == 'GET':
        message = 'EDIT MEASURE: GET form for page edit: %s' % form.data
    if request.method == 'POST':
        message = 'EDIT MEASURE: POST form for page edit: %s' % form.data
    current_app.logger.info(message)

    if 'save-and-review' in request.form:
        form.frequency_id.validators = [Optional()]

    saved = False
    if form.validate_on_submit():
        try:
            # this subtopic stuff is a bit stupid but they insist in loading more nonsense into this form
            # the original design was move was a separate activity not bundled up with edit
            form_data = form.data
            form_data['subtopic'] = request.form.get('subtopic', None)
            page_service.update_page(measure_page, data=form_data, last_updated_by=current_user.email)
            message = 'Updated page "{}"'.format(measure_page.title)
            current_app.logger.info(message)
            flash(message, 'info')
            saved = True
        except PageExistsException as e:
            current_app.logger.info(e)
            flash(str(e), 'error')
            form.title.data = measure_page.title
        except StaleUpdateException as e:
            current_app.logger.error(e)
            diffs = _diff_updates(form, measure_page)
            if diffs:
                flash('Your update will overwrite the latest content. Resolve the conflicts below', 'error')
            else:
                flash('Your update will overwrite the latest content. Reload this page', 'error')
        except PageUnEditable as e:
            current_app.logger.info(e)
            flash(str(e), 'error')

    if form.errors:
        message = 'This page could not be saved. Please check for errors below'
        flash(message, 'error')

    current_status = measure_page.status
    available_actions = measure_page.available_actions()
    if 'APPROVE' in available_actions:
        numerical_status = measure_page.publish_status(numerical=True)
        approval_state = publish_status.inv[(numerical_status + 1) % 6]

    if saved and 'save-and-review' in request.form:
        return redirect(url_for('cms.send_to_review',
                                topic=measure_page.parent.parent.guid,
                                subtopic=measure_page.parent.guid,
                                measure=measure_page.guid,
                                version=measure_page.version))
    elif saved:
        return redirect(url_for('cms.edit_measure_page',
                                topic=measure_page.parent.parent.guid,
                                subtopic=measure_page.parent.guid,
                                measure=measure_page.guid,
                                version=measure_page.version))
    context = {
        'form': form,
        'topic': measure_page.parent.parent,
        'subtopic': measure_page.parent,
        'measure': measure_page,
        'status': current_status,
        'available_actions': available_actions,
        'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
        'diffs': diffs,
        'organisations_by_type': Organisation.select_options_by_type(),
        'topics': topics
    }

    return render_template("cms/edit_measure_page.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/upload', methods=['GET', 'POST'])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_upload(topic, subtopic, measure, version):

    topic_page, subtopic_page, measure_page = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version
    )

    form = UploadForm()
    if request.method == 'POST':
        form = UploadForm(CombinedMultiDict((request.files, request.form)))
        if form.validate():
            f = form.upload.data
            try:
                upload = upload_service.create_upload(page=measure_page,
                                                      upload=f,
                                                      title=form.data['title'],
                                                      description=form.data['description'])

                message = 'Uploaded file "{}" to measure "{}"'.format(upload.title, measure)
                current_app.logger.info(message)
                flash(message, 'info')

            except (UploadCheckError, UploadAlreadyExists) as e:
                message = 'Error uploading file. {}'.format(str(e))
                current_app.logger.exception(e)
                flash(message, 'error')
                context = {"form": form,
                           "topic": topic_page,
                           "subtopic": subtopic_page,
                           "measure": measure_page
                           }
                return render_template("cms/create_upload.html", **context)

            return redirect(url_for("cms.edit_measure_page",
                                    topic=topic,
                                    subtopic=subtopic,
                                    measure=measure,
                                    version=version))

    context = {"form": form,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page
               }
    return render_template("cms/create_upload.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/send-to-review', methods=['GET'])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def send_to_review(topic, subtopic, measure, version):

    topic_page, subtopic_page, measure_page = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version
    )

    # in case user tries to directly GET this page
    if measure_page.status == 'DEPARTMENT_REVIEW':
        abort(400)

    if measure_page.type_of_data is not None:
        administrative_data = TypeOfData.ADMINISTRATIVE in measure_page.type_of_data
        survey_data = TypeOfData.SURVEY in measure_page.type_of_data
    else:
        administrative_data = survey_data = False

    if measure_page.area_covered is not None:
        if UKCountry.UK in measure_page.area_covered:
            england = wales = scotland = northern_ireland = True
        else:
            england = True if UKCountry.ENGLAND in measure_page.area_covered else False
            wales = True if UKCountry.WALES in measure_page.area_covered else False
            scotland = True if UKCountry.SCOTLAND in measure_page.area_covered else False
            northern_ireland = True if UKCountry.NORTHERN_IRELAND in measure_page.area_covered else False
    else:
        england = wales = scotland = northern_ireland = False

    form_to_validate = MeasurePageRequiredForm(obj=measure_page,
                                               meta={'csrf': False},
                                               administrative_data=administrative_data,
                                               survey_data=survey_data,
                                               frequency_choices=FrequencyOfRelease,
                                               type_of_statistic_choices=TypeOfStatistic,
                                               england=england,
                                               wales=wales,
                                               scotland=scotland,
                                               northern_ireland=northern_ireland,
                                               lowest_level_of_geography_choices=LowestLevelOfGeography)

    invalid_dimensions = []

    for dimension in measure_page.dimensions:
        dimension_form = DimensionRequiredForm(obj=dimension, meta={'csrf': False})
        if not dimension_form.validate():
            invalid_dimensions.append(dimension)

    if not form_to_validate.validate() or invalid_dimensions:
        # don't need to show user page has been saved when
        # required field validation failed.
        session.pop('_flashes', None)

        # Recreate form with csrf token for next update
        form = MeasurePageForm(obj=measure_page,
                               administrative_data=administrative_data,
                               survey_data=survey_data,
                               frequency_choices=FrequencyOfRelease,
                               type_of_statistic_choices=TypeOfStatistic,
                               england=england,
                               wales=wales,
                               scotland=scotland,
                               northern_ireland=northern_ireland,
                               lowest_level_of_geography_choices=LowestLevelOfGeography)

        for key, val in form_to_validate.errors.items():
            form.errors[key] = val
            field = getattr(form, key)
            field.errors = val
            setattr(form, key, field)

        message = 'Cannot submit for review, please see errors below'
        flash(message, 'error')
        if invalid_dimensions:
            for invalid_dimension in invalid_dimensions:
                message = 'Cannot submit for review ' \
                          '<a href="./%s/edit?validate=true">%s</a> dimension is not complete.' \
                          % (invalid_dimension.guid, invalid_dimension.title)
                flash(message, 'dimension-error')

        current_status = measure_page.status
        available_actions = measure_page.available_actions()
        if 'APPROVE' in available_actions:
            numerical_status = measure_page.publish_status(numerical=True)
            approval_state = publish_status.inv[numerical_status + 1]

        context = {
            'form': form,
            'topic': topic_page,
            'subtopic': subtopic_page,
            'measure': measure_page,
            'status': current_status,
            'available_actions': available_actions,
            'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
            'organisations_by_type': Organisation.select_options_by_type(),
            'topics': page_service.get_pages_by_type('topic')
        }

        return render_template("cms/edit_measure_page.html", **context)

    message = page_service.next_state(measure_page, updated_by=current_user.email)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/publish', methods=['GET'])
@login_required
@user_has_access
@user_can(PUBLISH)
def publish(topic, subtopic, measure, version):

    *_, measure_page = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version
    )

    if measure_page.status != 'DEPARTMENT_REVIEW':
        abort(400)

    message = page_service.next_state(measure_page, current_user.email)
    current_app.logger.info(message)
    _build_if_necessary(measure_page)
    flash(message, 'info')
    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/reject')
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def reject_page(topic, subtopic, measure, version):

    *_, measure_page = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version
    )

    # Can only reject if currently under review
    if measure_page.status != 'DEPARTMENT_REVIEW':
        abort(400)

    message = page_service.reject_page(measure, version)
    flash(message, 'info')
    current_app.logger.info(message)
    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/unpublish')
@login_required
@user_has_access
@user_can(PUBLISH)
def unpublish_page(topic, subtopic, measure, version):

    *_, measure_page = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version
    )

    # Can only unpublish if currently published
    if measure_page.status != 'APPROVED':
        abort(400)

    page, message = page_service.unpublish(measure, version, current_user.email)
    _build_if_necessary(page)
    flash(message, 'info')
    current_app.logger.info(message)
    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/draft')
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def send_page_to_draft(topic, subtopic, measure, version):

    _ = _get_measure_hierarchy_if_consistent_or_404(topic, subtopic, measure, version)

    message = page_service.send_page_to_draft(measure, version)
    flash(message, 'info')
    current_app.logger.info(message)
    return redirect(url_for("cms.edit_measure_page",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/dimension/new', methods=['GET', 'POST'])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_dimension(topic, subtopic, measure, version):

    topic_page, subtopic_page, measure_page = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version
    )

    form = DimensionForm()
    if request.method == 'POST':
        form = DimensionForm(request.form)

        messages = []
        if form.validate():
            try:
                dimension = dimension_service.create_dimension(page=measure_page,
                                                               title=form.data['title'],
                                                               time_period=form.data['time_period'],
                                                               summary=form.data['summary'],
                                                               ethnicity_category=form.data['ethnicity_category'],
                                                               include_parents=form.data['include_parents'],
                                                               include_all=form.data['include_all'],
                                                               include_unknown=form.data['include_unknown'])
                message = 'Created dimension "{}"'.format(dimension.title)
                flash(message, 'info')
                current_app.logger.info(message)
                return redirect(url_for("cms.edit_dimension",
                                        topic=topic,
                                        subtopic=subtopic,
                                        measure=measure,
                                        version=version,
                                        dimension=dimension.guid))
            except(DimensionAlreadyExists):
                message = 'Dimension with title "{}" already exists'.format(form.data['title'])
                flash(message, 'error')
                current_app.logger.error(message)
                return redirect(url_for("cms.create_dimension",
                                        topic=topic,
                                        subtopic=subtopic,
                                        measure=measure,
                                        version=version,
                                        messages=[{'message': 'Dimension with code %s already exists'
                                                              % form.data['title']}]))
        else:
            flash('Please complete all fields in the form', 'error')

    context = {"form": form,
               "create": True,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page,
               "categorisations_by_subfamily": categorisation_service.get_categorisations_by_family('Ethnicity')
               }
    return render_template("cms/create_dimension.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/edit', methods=['GET', 'POST'])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def edit_dimension(topic, subtopic, measure, version, dimension):

    topic_page, subtopic_page, measure_page, dimension_object = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version, dimension=dimension
    )

    current_cat_link = categorisation_service.get_categorisation_link_for_dimension_by_family(
        dimension=dimension_object,
        family='Ethnicity')

    if request.method == 'POST':
        form = DimensionForm(request.form)
        if form.validate():
            dimension_service.update_dimension(dimension=dimension_object, data=form.data)
            message = 'Updated dimension "{}" of measure "{}"'.format(dimension_object.title, measure)

            flash(message, 'info')
            return redirect(url_for('cms.edit_dimension',
                                    topic=topic,
                                    subtopic=subtopic,
                                    measure=measure,
                                    dimension=dimension,
                                    version=version))

    else:
        form = DimensionForm(obj=dimension_object,
                             ethnicity_category=current_cat_link.categorisation_id if current_cat_link else -1,
                             include_parents=current_cat_link.includes_parents if current_cat_link else False,
                             include_all=current_cat_link.includes_all if current_cat_link else False,
                             include_unknown=current_cat_link.includes_unknown if current_cat_link else False)

    context = {"form": form,
               "topic": topic_page,
               "subtopic": subtopic_page,
               "measure": measure_page,
               "dimension": dimension_object,
               "categorisations_by_subfamily": categorisation_service.get_categorisations_by_family('Ethnicity'),
               "current_categorisation": current_cat_link.categorisation_id if current_cat_link else -1
               }

    return render_template("cms/edit_dimension.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/chartbuilder')
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def chartbuilder(topic, subtopic, measure, version, dimension):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    dimension_dict = dimension_object.to_dict()

    if 'chart_builder_version' in dimension_dict and dimension_dict['chart_builder_version'] == 1:
        return redirect(
            url_for("cms.create_chart_original", topic=topic, subtopic=subtopic, measure=measure, version=version,
                    dimension=dimension))

    return redirect(url_for("cms.create_chart", topic=topic, subtopic=subtopic, measure=measure, version=version,
                            dimension=dimension))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/create-chart')
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_chart(topic, subtopic, measure, version, dimension):

    topic_page, subtopic_page, measure_page, dimension_object = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version, dimension=dimension
    )

    dimension_dict = dimension_object.to_dict()

    if dimension_dict['chart_source_data'] is not None and dimension_dict['chart_2_source_data'] is None:
        dimension_dict['chart_2_source_data'] = ChartObjectDataBuilder.upgrade_v1_to_v2(dimension_dict['chart'],
                                                                                        dimension_dict[
                                                                                            'chart_source_data'])

    context = {'topic': topic_page,
               'subtopic': subtopic_page,
               'measure': measure_page,
               'dimension': dimension_dict}

    return render_template("cms/create_chart_2.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/create-chart/advanced')
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_chart_original(topic, subtopic, measure, version, dimension):
    try:
        measure_page = page_service.get_page_with_version(measure, version)
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        dimension_object = measure_page.get_dimension(dimension)
    except PageNotFoundException:
        abort(404)
    except DimensionNotFoundException:
        abort(404)

    context = {'topic': topic_page,
               'subtopic': subtopic_page,
               'measure': measure_page,
               'dimension': dimension_object.to_dict()}

    return render_template("cms/create_chart.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/create_table')
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_table(topic, subtopic, measure, version, dimension):

    topic_page, subtopic_page, measure_page, dimension_object = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version, dimension=dimension
    )

    context = {'topic': topic_page,
               'subtopic': subtopic_page,
               'measure': measure_page,
               'dimension': dimension_object.to_dict()}

    return render_template("cms/create_table.html", **context)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/save_chart', methods=["POST"])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def save_chart_to_page(topic, subtopic, measure, version, dimension):

    *_, measure_page, dimension_object = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version, dimension=dimension
    )

    if measure_page.not_editable():
        message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(measure_page.guid)
        current_app.logger.exception(message)
        raise PageUnEditable(message)

    chart_json = request.json

    dimension_service.update_measure_dimension(dimension_object, chart_json)

    message = 'Updated chart on dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return jsonify({"success": True})


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/delete_chart')
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def delete_chart(topic, subtopic, measure, version, dimension):

    *_, measure_page, dimension_object = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version, dimension=dimension
    )

    dimension_service.delete_chart(dimension_object)

    message = 'Deleted chart from dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_dimension",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version,
                            dimension=dimension_object.guid))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/save_table', methods=["POST"])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def save_table_to_page(topic, subtopic, measure, version, dimension):

    *_, measure_page, dimension_object = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version, dimension=dimension
    )

    if measure_page.not_editable():
        message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(measure_page.guid)
        current_app.logger.exception(message)
        raise PageUnEditable(message)

    table_json = request.json

    dimension_service.update_measure_dimension(dimension_object, table_json)

    message = 'Updated table on dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return jsonify({"success": True})


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/<dimension>/delete_table')
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def delete_table(topic, subtopic, measure, version, dimension):

    *_, measure_page, dimension_object = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version, dimension=dimension
    )

    dimension_service.delete_table(dimension_object)

    message = 'Deleted table from dimension "{}" of measure "{}"'.format(dimension_object.title, measure)
    current_app.logger.info(message)
    flash(message, 'info')

    return redirect(url_for("cms.edit_dimension",
                            topic=topic,
                            subtopic=subtopic,
                            measure=measure,
                            version=version,
                            dimension=dimension_object.guid))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/uploads', methods=['GET'])
@login_required
def get_measure_page_uploads(topic, subtopic, measure, version):

    *_, measure_page = _get_measure_hierarchy_if_consistent_or_404(topic, subtopic, measure, version)
    uploads = upload_service.get_page_uploads(measure_page) or {}
    return json.dumps({'uploads': uploads}), 200


def _build_is_required(page, req, beta_publication_states):
    if page.status == 'UNPUBLISH':
        return True
    if get_bool(req.args.get('build')) and page.eligible_for_build(beta_publication_states):
        return True
    return False


@cms_blueprint.route('/data_processor', methods=['POST'])
@login_required
def process_input_data():
    if current_app.harmoniser:
        request_json = request.json
        return_data = current_app.harmoniser.process_data(request_json['data'])
        return json.dumps({'data': return_data}), 200
    else:
        return json.dumps(request.json), 200


@cms_blueprint.route('/get-valid-presets-for-data', methods=['POST'])
@login_required
def process_auto_data():
    """
    This is an AJAX endpoint for the AutoDataGenerator data standardiser

    It is called whenever data needs to be cleaned up for use in second generation front end data tools
    (chartbuilder 2 & potentially tablebuilder 2)

    :return: A list of processed versions of input data using different "presets"
    """
    if current_app.auto_data_generator:
        request_json = request.json
        return_data = current_app.auto_data_generator.build_auto_data(request_json['data'])
        return json.dumps({'presets': return_data}), 200
    else:
        return json.dumps(request.json), 200


# TODO: Figure out if this endpoint really needs to take topic/subtopic/measure?
# * If so, it should also take version and call _get_measure_hierarchy_if_consistent_or_404
# * If not, refactor to remove these parameters from the url and call signature
@cms_blueprint.route('/<topic>/<subtopic>/<measure>/set-dimension-order', methods=['POST'])
@login_required
def set_dimension_order(topic, subtopic, measure):
    dimensions = request.json.get('dimensions', [])
    try:
        dimension_service.set_dimension_positions(dimensions)
        return json.dumps({'status': 'OK', 'status_code': 200}), 200
    except Exception as e:
        return json.dumps({'status': 'INTERNAL SERVER ERROR', 'status_code': 500}), 500


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/versions')
@login_required
@user_has_access
def list_measure_page_versions(topic, subtopic, measure):
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
    except PageNotFoundException:
        current_app.logger.exception('Page id: {} not found'.format(measure))
        abort(404)
    measures = page_service.get_measure_page_versions(subtopic, measure)
    measures.sort(reverse=True)
    if not measures:
        return redirect(url_for('cms.subtopic', topic=topic, subtopic=subtopic))
    measure_title = measures[0].title if measures else ''
    return render_template('cms/measure_page_versions.html',
                           topic=topic_page,
                           subtopic=subtopic_page,
                           measures=measures,
                           measure_title=measure_title)


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/delete')
@login_required
@user_can(DELETE_MEASURE)
def delete_measure_page(topic, subtopic, measure, version):

    topic_page, *_ = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version
    )

    page_service.delete_measure_page(measure, version)
    if request.referrer.endswith('/versions'):
        return redirect(url_for('cms.list_measure_page_versions', topic=topic, subtopic=subtopic, measure=measure))
    else:
        return redirect(url_for('static_site.topic', uri=topic_page.uri))


@cms_blueprint.route('/<topic>/<subtopic>/<measure>/<version>/new-version', methods=['GET', 'POST'])
@login_required
@user_can(CREATE_VERSION)
def new_version(topic, subtopic, measure, version):

    topic_page, subtopic_page, measure_page = _get_measure_hierarchy_if_consistent_or_404(
        topic, subtopic, measure, version
    )

    form = NewVersionForm()
    if form.validate_on_submit():
        version_type = form.data['version_type']
        try:
            page = page_service.create_copy(measure, version, version_type, created_by=current_user.email)
            message = 'Added a new %s version %s' % (version_type, page.version)
            flash(message)
            return redirect(url_for("cms.edit_measure_page",
                                    topic=topic_page.guid,
                                    subtopic=subtopic_page.guid,
                                    measure=page.guid,
                                    version=page.version))
        except UpdateAlreadyExists as e:
            message = 'Version %s of page %s is already being updated' % (version, measure)
            flash(message, 'error')
            return redirect(url_for('cms.new_version',
                                    topic=topic,
                                    subtopic=subtopic,
                                    measure=measure,
                                    version=version,
                                    form=form))

    return render_template('cms/create_new_version.html',
                           topic=topic_page,
                           subtopic=subtopic_page,
                           measure=measure_page,
                           form=form)


@cms_blueprint.route('/set-measure-order', methods=['POST'])
@login_required
def set_measure_order():
    from application import db
    try:
        positions = request.json.get('positions', [])
        for p in positions:
            pages = Page.query.filter_by(guid=p['guid'], parent_guid=p['subtopic']).all()
            for page in pages:
                page.position = p['position']
                db.session.add(page)
        db.session.commit()
        request_build()
        return json.dumps({'status': 'OK', 'status_code': 200}), 200
    except Exception as e:
        current_app.logger.exception(e)
        return json.dumps({'status': 'INTERNAL SERVER ERROR', 'status_code': 500}), 500


def _build_if_necessary(page):
    if page.status == 'UNPUBLISH':
        build_service.request_build()
    elif page.eligible_for_build():
        page_service.mark_page_published(page)
        build_service.request_build()


def _get_measure_hierarchy_if_consistent_or_404(topic, subtopic, measure, version, dimension=None, upload=None):
    try:
        topic_page = page_service.get_page(topic)
        subtopic_page = page_service.get_page(subtopic)
        measure_page = page_service.get_page_with_version(measure, version)
        dimension_object = measure_page.get_dimension(dimension) if dimension else None
        upload_object = measure_page.get_upload(upload) if upload else None
    except PageNotFoundException:
        current_app.logger.exception('Page id: {} not found'.format(measure))
        abort(404)
    except UploadNotFoundException:
        current_app.logger.exception('Upload id: {} not found'.format(upload))
        abort(404)
    except DimensionNotFoundException:
        current_app.logger.exception('Dimension id: {} not found'.format(dimension))
        abort(404)

    # Check the topic and subtopics in the URL are the right ones for the measure
    if measure_page.parent != subtopic_page or measure_page.parent.parent != topic_page:
        abort(404)

    # Check the dimension belongs to the measure
    if dimension_object and (
            dimension_object.page_id != measure_page.guid or dimension_object.page_version != measure_page.version
    ):
        abort(404)

    # Check the upload belongs to the measure
    if upload_object and (
            upload_object.page_id != measure_page.guid or upload_object.page_version != measure_page.version
    ):
        abort(404)

    return_items = [topic_page, subtopic_page, measure_page]
    if dimension_object:
        return_items.append(dimension_object)
    if upload_object:
        return_items.append(upload_object)

    return (item for item in return_items)
