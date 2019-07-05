import json


from flask import redirect, render_template, request, url_for, abort, flash, current_app, jsonify, session
from flask_login import login_required, current_user
from werkzeug.datastructures import CombinedMultiDict

from application.auth.models import (
    COPY_MEASURE,
    CREATE_MEASURE,
    CREATE_VERSION,
    DELETE_MEASURE,
    PUBLISH,
    UPDATE_MEASURE,
)
from application.cms import cms_blueprint
from application.cms.dimension_service import dimension_service
from application.cms.exceptions import (
    PageNotFoundException,
    DimensionAlreadyExists,
    PageExistsException,
    UpdateAlreadyExists,
    UploadCheckError,
    StaleUpdateException,
    UploadAlreadyExists,
    PageUnEditable,
)
from application.cms.forms import (
    DimensionForm,
    DimensionRequiredForm,
    MeasureVersionForm,
    NewUploadForm,
    NewVersionForm,
    UploadForm,
    DataSourceForm,
)
from application.cms.models import NewVersionType, MeasureVersion, Measure
from application.cms.models import Organisation, DataSource
from application.cms.page_service import page_service
from application.cms.upload_service import upload_service
from application.cms.utils import copy_form_errors, get_form_errors, ErrorSummaryMessage, TextFieldDiff
from application.sitebuilder import build_service
from application.utils import get_bool, user_can, user_has_access

from application import db


@cms_blueprint.route("")
@login_required
def index():
    return redirect(url_for("static_site.index"))


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/measure/new", methods=["GET", "POST"])
@login_required
@user_can(CREATE_MEASURE)
def create_measure(topic_slug, subtopic_slug):
    try:
        topic = page_service.get_topic(topic_slug)
        subtopic = page_service.get_subtopic(topic_slug, subtopic_slug)
    except PageNotFoundException:
        abort(404)

    form = MeasureVersionForm(
        is_minor_update=False,
        internal_edit_summary="Initial version",
        external_edit_summary="First published",
        previous_minor_versions=tuple(),
    )

    if form.validate_on_submit():
        try:
            new_measure_version = page_service.create_measure(
                subtopic=subtopic, measure_version_form=form, created_by_email=current_user.email
            )

            message = "Created page {}".format(new_measure_version.title)
            flash(message, "info")
            current_app.logger.info(message)
            return redirect(
                url_for(
                    "cms.edit_measure_version",
                    topic_slug=topic.slug,
                    subtopic_slug=subtopic.slug,
                    measure_slug=new_measure_version.measure.slug,
                    version=new_measure_version.version,
                )
            )
        except PageExistsException as e:
            message = str(e)
            flash(message, "error")
            current_app.logger.error(message)
            return redirect(
                url_for("cms.create_measure", form=form, topic_slug=topic.slug, subtopic_slug=subtopic.slug)
            )

    return render_template(
        "cms/edit_measure_version.html",
        form=form,
        topic=topic,
        subtopic=subtopic,
        measure=Measure(),
        measure_version=MeasureVersion(),
        new=True,
        organisations_by_type=Organisation.select_options_by_type(),
        topics=page_service.get_topics(include_testing_space=True),
        errors=get_form_errors(forms=(form,)),
        data_not_uploaded_error=False,
        data_sources_not_added=False,
        dimensions_not_complete_error=False,
    )


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/uploads/<upload_guid>/delete", methods=["POST"]
)
@login_required
@user_has_access
def delete_upload(topic_slug, subtopic_slug, measure_slug, version, upload_guid):
    *_, measure_version, upload_object = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, upload_guid=upload_guid
    )

    upload_service.delete_upload_obj(measure_version, upload_object)

    message = "Deleted upload ‘{}’".format(upload_object.title)
    current_app.logger.info(message)
    flash(message, "info")

    return redirect(
        url_for(
            "cms.edit_measure_version",
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug,
            measure_slug=measure_slug,
            version=version,
        )
    )


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/uploads/<upload_guid>/edit", methods=["GET", "POST"]
)
@login_required
@user_has_access
def edit_upload(topic_slug, subtopic_slug, measure_slug, version, upload_guid):
    topic, subtopic, measure, measure_version, upload_object = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, upload_guid=upload_guid
    )

    form = UploadForm(obj=upload_object)

    if request.method == "POST":
        form = UploadForm(CombinedMultiDict((request.files, request.form)))
        if form.validate():
            file_data = form.upload.data if form.upload.data else None
            try:
                upload_service.edit_upload(
                    measure_version=measure_version, upload=upload_object, file=file_data, data=form.data
                )
                message = "Updated upload {}".format(upload_object.title)
                flash(message, "info")
                return redirect(
                    url_for(
                        "cms.edit_measure_version",
                        topic_slug=topic.slug,
                        subtopic_slug=subtopic.slug,
                        measure_slug=measure.slug,
                        version=measure_version.version,
                    )
                )
            except UploadCheckError as e:
                message = "Error uploading file. {}".format(str(e))
                current_app.logger.exception(e)
                flash(message, "error")

    context = {
        "form": form,
        "topic": topic,
        "subtopic": subtopic,
        "measure": measure,
        "measure_version": measure_version,
        "upload": upload_object,
    }
    return render_template("cms/edit_upload.html", **context)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/delete", methods=["POST"])
@login_required
@user_has_access
def delete_dimension(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    *_, measure_version, dimension_object = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_service.delete_dimension(measure_version, dimension_object.guid)

    message = "Deleted dimension ‘{}’".format(dimension_object.title)
    current_app.logger.info(message)
    flash(message, "info")

    return redirect(
        url_for(
            "cms.edit_measure_version",
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug,
            measure_slug=measure_slug,
            version=version,
        )
    )


def _diff_updates(form, page):
    from lxml.html.diff import htmldiff
    from flask import escape
    from markupsafe import Markup

    diffs = {}
    for k, v in form.data.items():
        if hasattr(page, k) and k != "db_version_id":
            page_value = getattr(page, k)
            if v is not None and page_value is not None:
                diff = htmldiff(escape(str(page_value).rstrip()), escape(str(v).rstrip()))
                if "<ins>" in diff or "<del>" in diff:
                    getattr(form, k).errors.append(
                        f"‘{getattr(form, k).label.text}’ has been updated by {page.last_updated_by}"
                    )

                    # The resulting diff has had the user-input escaped, but does contain <ins> and <del> tags that
                    # need to be rendered without being escaped. So we should consider the diff as safe Markup.
                    diffs[k] = TextFieldDiff(diff_markup=Markup(diff), updated_by=page.last_updated_by)

    form.db_version_id.data = page.db_version_id
    return diffs


@cms_blueprint.route(  # noqa: C901 (complexity)
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/edit", methods=["GET", "POST"]
)
@login_required
@user_has_access
def edit_measure_version(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    # These actions are changes of state sent by buttons in the top banner of the measure page.
    # The buttons are embedded inside the measure page form and we POST here to get the benefit of CSRF protection.
    # They don't require the form to be validated or saved so we check for them first and redirect as appropriate.
    measure_action = request.form.get("measure-action", False)
    if request.method == "POST" and measure_action:
        redirect_following_change_of_status = redirect(
            url_for(
                "cms.edit_measure_version",
                topic_slug=topic_slug,
                subtopic_slug=subtopic_slug,
                measure_slug=measure_slug,
                version=version,
            )
        )
        if measure_action == "reject-measure":
            _reject_page(topic_slug=topic_slug, subtopic_slug=subtopic_slug, measure_slug=measure_slug, version=version)
            return redirect_following_change_of_status

        elif measure_action == "send-back-to-draft":
            _send_page_to_draft(
                topic_slug=topic_slug, subtopic_slug=subtopic_slug, measure_slug=measure_slug, version=version
            )
            return redirect_following_change_of_status

        elif measure_action == "send-to-department-review":
            return _send_to_review(
                topic_slug=topic_slug, subtopic_slug=subtopic_slug, measure_slug=measure_slug, version=version
            )

        elif measure_action == "send-to-approved":
            _publish(topic_slug=topic_slug, subtopic_slug=subtopic_slug, measure_slug=measure_slug, version=version)
            return redirect_following_change_of_status

    diffs = {}

    if request.method == "GET":
        measure_version_form = MeasureVersionForm(
            is_minor_update=measure_version.is_minor_version(), obj=measure_version
        )
    elif request.method == "POST":
        measure_version_form = MeasureVersionForm(
            is_minor_update=measure_version.is_minor_version(),
            previous_minor_versions=measure_version.previous_minor_versions,
        )

    saved = False
    errors_preamble = None
    if measure_version_form.validate_on_submit():
        additional_kwargs_from_request = {
            "status": request.form.get("status", None),
            "subtopic_id": request.form.get("subtopic", None),
        }
        try:
            page_service.update_measure_version(
                measure_version,
                measure_version_form=measure_version_form,
                last_updated_by_email=current_user.email,
                **additional_kwargs_from_request,
            )
            message = 'Updated page "{}"'.format(measure_version.title)
            current_app.logger.info(message)
            flash(message, "info")
            saved = True
        except PageExistsException as e:
            current_app.logger.info(e)
            flash(str(e), "error")
            measure_version_form.title.data = measure_version.title
        except StaleUpdateException as e:
            current_app.logger.error(e)
            diffs = _diff_updates(measure_version_form, measure_version)
            if diffs:
                errors_preamble = (
                    "Your update will overwrite updates made by other people. "
                    "Only save the page after reviewing all of the following:"
                )

                # Need to manually update the `db_version_id`, otherwise when the form is re-submitted it will just
                # throw the same error.
                measure_version_form.db_version_id.raw_data = [str(measure_version.db_version_id)]
            else:
                errors_preamble = (
                    "Your update will overwrite updates made by other people. "
                    "Reload this page and re-enter your update."
                )

        except PageUnEditable as e:
            current_app.logger.info(e)
            flash(str(e), "error")

    if saved and "save-and-review" in request.form:
        return _send_to_review(
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    elif saved:
        return redirect(
            url_for(
                "cms.edit_measure_version",
                topic_slug=measure_version.measure.subtopic.topic.slug,
                subtopic_slug=measure_version.measure.subtopic.slug,
                measure_slug=measure_version.measure.slug,
                version=measure_version.version,
            )
        )
    context = {
        "form": measure_version_form,
        "topic": measure_version.measure.subtopic.topic,
        "subtopic": measure_version.measure.subtopic,
        "measure": measure_version.measure,
        "measure_version": measure_version,
        "diffs": diffs,
        "organisations_by_type": Organisation.select_options_by_type(),
        "topics": page_service.get_topics(include_testing_space=True),
        "errors_preamble": errors_preamble,
        "errors": get_form_errors(forms=[measure_version_form]),
        "new": False,
        "data_not_uploaded_error": False,
        "data_sources_not_added": False,
        "dimensions_not_complete_error": False,
    }

    return render_template("cms/edit_measure_version.html", **context)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/upload", methods=["GET", "POST"])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_upload(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    if request.method == "POST":
        form = NewUploadForm(CombinedMultiDict((request.files, request.form)))
        if form.validate():
            file_data = form.upload.data
            try:
                upload = upload_service.create_upload(
                    measure_version=measure_version,
                    upload=file_data,
                    title=form.data["title"],
                    description=form.data["description"],
                )

                message = 'Uploaded file "{}" to measure "{}"'.format(upload.title, measure_slug)
                current_app.logger.info(message)
                flash(message, "info")

            except (UploadCheckError, UploadAlreadyExists) as e:
                message = "Error uploading file. {}".format(str(e))
                current_app.logger.exception(e)
                flash(message, "error")
                context = {
                    "form": form,
                    "topic": topic,
                    "subtopic": subtopic,
                    "measure": measure,
                    "measure_version": measure_version,
                }
                return render_template("cms/create_upload.html", **context)

            return redirect(
                url_for(
                    "cms.edit_measure_version",
                    topic_slug=topic.slug,
                    subtopic_slug=subtopic.slug,
                    measure_slug=measure.slug,
                    version=measure_version.version,
                )
            )
    else:
        form = NewUploadForm()

    context = {
        "form": form,
        "topic": topic,
        "subtopic": subtopic,
        "measure": measure,
        "measure_version": measure_version,
    }
    return render_template("cms/create_upload.html", **context)


def _send_to_review(topic_slug, subtopic_slug, measure_slug, version):  # noqa: C901 (complexity) TODO: split out funcs
    if not current_user.can(UPDATE_MEASURE):
        abort(403)
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    if measure_version.status == "DEPARTMENT_REVIEW":
        abort(400, "This page is already under departmental review.")

    #  No need to validate if page is already under review, as it has already been validated
    if measure_version.status != "INTERNAL_REVIEW":

        measure_version_form_to_validate = MeasureVersionForm(
            is_minor_update=measure_version.is_minor_version(),
            obj=measure_version,
            meta={"csrf": False},
            sending_to_review=True,
        )

        invalid_dimensions = []
        for dimension in measure_version.dimensions:
            dimension_form = DimensionRequiredForm(obj=dimension, meta={"csrf": False})
            if not dimension_form.validate():
                invalid_dimensions.append(dimension)

        measure_version_form_validated = measure_version_form_to_validate.validate()

        # Measure versions should have a data file uploaded before sending to review
        data_file_uploaded = len(measure_version.uploads) > 0

        if (
            not measure_version_form_validated
            or invalid_dimensions
            or not data_file_uploaded
            or not measure_version.data_sources
        ):
            # don't need to show user page has been saved when
            # required field validation failed.
            session.pop("_flashes", None)

            # Recreate form with csrf token for next update
            measure_version_form = MeasureVersionForm(
                is_minor_update=measure_version.is_minor_version(), obj=measure_version
            )

            # If the page was saved before sending to review form's db_version_id will be out of sync, so update it
            measure_version_form.db_version_id.raw_data = [str(measure_version.db_version_id)]

            copy_form_errors(from_form=measure_version_form_to_validate, to_form=measure_version_form)

            additional_errors = []
            data_not_uploaded_error = dimensions_not_complete_error = data_sources_not_added = False
            if invalid_dimensions:
                dimensions_not_complete_error = True
                for invalid_dimension in invalid_dimensions:
                    additional_errors.append(
                        ErrorSummaryMessage(
                            text="Your dimension is missing a title. Enter a title.",
                            href=f"./{invalid_dimension.guid}/edit?validate=true",
                        )
                    )

            if not data_file_uploaded:
                data_not_uploaded_error = True
                additional_errors.append(ErrorSummaryMessage(text="Upload the source data", href="#source-data"))

            if not measure_version.data_sources:
                data_sources_not_added = True
                additional_errors.append(ErrorSummaryMessage(text="Add at least one data source", href="#data-sources"))

            context = {
                "form": measure_version_form,
                "topic": topic,
                "subtopic": subtopic,
                "measure": measure_version.measure,
                "measure_version": measure_version,
                "organisations_by_type": Organisation.select_options_by_type(),
                "topics": page_service.get_topics(include_testing_space=True),
                "errors": get_form_errors(forms=[measure_version_form], extra_non_form_errors=additional_errors),
                "data_not_uploaded_error": data_not_uploaded_error,
                "data_sources_not_added": data_sources_not_added,
                "dimensions_not_complete_error": dimensions_not_complete_error,
                "new": False,
            }

            return render_template("cms/edit_measure_version.html", **context), 400

    message = page_service.move_measure_version_to_next_state(measure_version, updated_by=current_user.email)
    current_app.logger.info(message)
    flash(message, "info")

    return redirect(
        url_for(
            "cms.edit_measure_version",
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug,
            measure_slug=measure_slug,
            version=version,
        )
    )


def _publish(topic_slug, subtopic_slug, measure_slug, version):
    if not current_user.can(PUBLISH):
        abort(403)
    *_, measure_version = page_service.get_measure_version_hierarchy(topic_slug, subtopic_slug, measure_slug, version)

    if measure_version.status != "DEPARTMENT_REVIEW":
        abort(400, "This page can not be published until it has been through departmental review.")

    message = page_service.move_measure_version_to_next_state(measure_version, current_user.email)
    current_app.logger.info(message)
    _build_if_necessary(measure_version)
    flash(message, "info")


def _reject_page(topic_slug, subtopic_slug, measure_slug, version):
    if not current_user.can(UPDATE_MEASURE):
        abort(403)
    *_, measure_version = page_service.get_measure_version_hierarchy(topic_slug, subtopic_slug, measure_slug, version)

    # Can only reject if currently under review
    if measure_version.status not in {"INTERNAL_REVIEW", "DEPARTMENT_REVIEW"}:
        abort(400, "This page can not be rejected because it is not currently under review.")

    message = page_service.reject_measure_version(measure_version)
    flash(message, "info")
    current_app.logger.info(message)


def _send_page_to_draft(topic_slug, subtopic_slug, measure_slug, version):
    if not current_user.can(UPDATE_MEASURE):
        abort(403)
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    message = page_service.send_measure_version_to_draft(measure_version)
    flash(message, "info")
    current_app.logger.info(message)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/dimension/new", methods=["GET", "POST"])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_dimension(topic_slug, subtopic_slug, measure_slug, version):
    if request.method == "POST":
        return _post_create_dimension(topic_slug, subtopic_slug, measure_slug, version)
    else:
        return _get_create_dimension(topic_slug, subtopic_slug, measure_slug, version)


def _post_create_dimension(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )
    form = DimensionForm(request.form)

    if form.validate():
        try:
            dimension = dimension_service.create_dimension(
                measure_version=measure_version,
                title=form.data["title"],
                time_period=form.data["time_period"],
                summary=form.data["summary"],
            )
            message = 'Created dimension "{}"'.format(dimension.title)
            flash(message, "info")
            current_app.logger.info(message)
            return redirect(
                url_for(
                    "cms.edit_dimension",
                    topic_slug=topic_slug,
                    subtopic_slug=subtopic_slug,
                    measure_slug=measure_slug,
                    version=version,
                    dimension_guid=dimension.guid,
                )
            )
        except DimensionAlreadyExists:
            message = 'Dimension with title "{}" already exists'.format(form.data["title"])
            flash(message, "error")
            current_app.logger.error(message)
            return redirect(
                url_for(
                    "cms.create_dimension",
                    topic_slug=topic_slug,
                    subtopic_slug=subtopic_slug,
                    measure_slug=measure_slug,
                    version=version,
                    messages=[{"message": "Dimension with code %s already exists" % form.data["title"]}],
                )
            )

    return _get_create_dimension(topic_slug, subtopic_slug, measure_slug, version, form=form)


def _get_create_dimension(topic_slug, subtopic_slug, measure_slug, version, form=None):
    form = form if form is not None else DimensionForm()

    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    return render_template(
        "cms/create_dimension.html",
        form=form,
        create=True,
        topic=topic,
        subtopic=subtopic,
        measure=measure,
        measure_version=measure_version,
        errors=get_form_errors(forms=(form,)),
    )


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/edit", methods=["GET", "POST"]
)
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def edit_dimension(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    if request.method == "POST":
        return _post_edit_dimension(request, topic_slug, subtopic_slug, measure_slug, dimension_guid, version)
    else:
        return _get_edit_dimension(topic_slug, subtopic_slug, measure_slug, dimension_guid, version)


def _post_edit_dimension(request, topic_slug, subtopic_slug, measure_slug, dimension_guid, version):

    form = DimensionForm(request.form)
    topic, subtopic, measure, measure_version, dimension_object = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    if form.validate():
        dimension_service.update_dimension(dimension=dimension_object, data=form.data)
        message = 'Updated dimension "{}" of measure "{}"'.format(dimension_object.title, measure_slug)

        flash(message, "info")
        return redirect(
            url_for(
                "cms.edit_dimension",
                topic_slug=topic_slug,
                subtopic_slug=subtopic_slug,
                measure_slug=measure_slug,
                dimension_guid=dimension_guid,
                version=version,
            )
        )
    else:
        return _get_edit_dimension(
            topic.slug, subtopic.slug, measure.slug, dimension_object.guid, measure_version.version, form=form
        )


def _get_edit_dimension(topic_slug, subtopic_slug, measure_slug, dimension_guid, version, form=None):
    topic, subtopic, measure, measure_version, dimension_object = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_classification = dimension_object.dimension_classification

    if form is None:
        form = DimensionForm(obj=dimension_object)

    errors = get_form_errors(forms=(form,))

    context = {
        "form": form,
        "topic": topic,
        "subtopic": subtopic,
        "measure": measure,
        "measure_version": measure_version,
        "dimension": dimension_object,
        "ethnicity_classification": dimension_classification.classification.long_title
        if dimension_classification
        else None,
        "includes_all": dimension_classification.includes_all if dimension_classification else None,
        "includes_parents": dimension_classification.includes_parents if dimension_classification else None,
        "includes_unknown": dimension_classification.includes_unknown if dimension_classification else None,
        "classification_source": dimension_object.classification_source_string,
        "errors": errors,
    }

    return render_template("cms/edit_dimension.html", **context), 400 if errors else 200


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/create-chart")
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_chart(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    topic, subtopic, measure, measure_version, dimension = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    return render_template(
        "cms/create_chart.html",
        topic=topic,
        subtopic=subtopic,
        measure=measure,
        measure_version=measure_version,
        dimension=dimension,
        classification_options=__get_classification_finder_classifications(),
    )


def __get_classification_finder_classifications():
    classification_collection = current_app.classification_finder.get_classification_collection()
    classifications = classification_collection.get_sorted_classifications()
    return [{"code": classification.get_id(), "name": classification.get_name()} for classification in classifications]


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/create-table")
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_table(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    topic, subtopic, measure, measure_version, dimension = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    return render_template(
        "cms/create_table.html",
        topic=topic,
        subtopic=subtopic,
        measure=measure,
        measure_version=measure_version,
        dimension=dimension,
        classification_options=__get_classification_finder_classifications(),
    )


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/save-chart", methods=["POST"]
)
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def save_chart_to_page(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    *_, measure_version, dimension_object = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    if measure_version.not_editable():
        message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(measure_version.title)
        current_app.logger.exception(message)
        raise PageUnEditable(message)

    chart_json = request.json

    dimension_service.update_dimension_chart_or_table(dimension_object, chart_json)

    message = 'Updated chart on dimension "{}" of measure "{}"'.format(dimension_object.title, measure_slug)
    current_app.logger.info(message)
    flash(message, "info")

    return jsonify({"success": True})


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/delete-chart", methods=["POST"]
)
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def delete_chart(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    *_, measure_version, dimension_object = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_object.dimension_chart.delete()

    message = "Deleted chart from dimension ‘{}’ of measure ‘{}’".format(dimension_object.title, measure_version.title)
    current_app.logger.info(message)
    flash(message, "info")

    return redirect(
        url_for(
            "cms.edit_dimension",
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug,
            measure_slug=measure_slug,
            version=measure_version.version,
            dimension_guid=dimension_object.guid,
        )
    )


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/save-table", methods=["POST"]
)
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def save_table_to_page(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    *_, measure_version, dimension_object = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    if measure_version.not_editable():
        message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(measure_version.title)
        current_app.logger.exception(message)
        raise PageUnEditable(message)

    table_json = request.json

    dimension_service.update_dimension_chart_or_table(dimension_object, table_json)

    message = 'Updated table on dimension "{}" of measure "{}"'.format(dimension_object.title, measure_slug)
    current_app.logger.info(message)
    flash(message, "info")

    return jsonify({"success": True})


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/delete-table", methods=["POST"]
)
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def delete_table(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    *_, measure_version, dimension_object = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_object.dimension_table.delete()

    message = "Deleted table from dimension ‘{}’ of measure ‘{}’".format(dimension_object.title, measure_version.title)
    current_app.logger.info(message)
    flash(message, "info")

    return redirect(
        url_for(
            "cms.edit_dimension",
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug,
            measure_slug=measure_slug,
            version=measure_version.version,
            dimension_guid=dimension_object.guid,
        )
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/uploads", methods=["GET"])
@login_required
def get_measure_version_uploads(topic_slug, subtopic_slug, measure_slug, version):
    *_, measure_version = page_service.get_measure_version_hierarchy(topic_slug, subtopic_slug, measure_slug, version)

    uploads = upload_service.get_page_uploads(measure_version) or {}
    return json.dumps({"uploads": uploads}), 200


def _build_is_required(page, req, beta_publication_states):
    if get_bool(req.args.get("build")) and page.eligible_for_build(beta_publication_states):
        return True
    return False


@cms_blueprint.route("/get-valid-classifications-for-data", methods=["POST"])
@login_required
def get_valid_classifications():
    """
    This is an AJAX endpoint for the EthnicityClassificationFinder data standardiser

    It cleans up data and identifies possible ethnicity classifications in use for chartbuilder and tablebuilder

    :return: A list of processed versions of input data using different "classifications"
    """
    request_data = request.json["data"]
    valid_classifications_data = current_app.classification_finder.find_classifications(request_data)

    return json.dumps({"classifications": valid_classifications_data}), 200


@cms_blueprint.route("/set-dimension-order", methods=["POST"])
@login_required
def set_dimension_order():
    dimensions = request.json.get("dimensions", [])
    try:
        dimension_service.set_dimension_positions(dimensions)
        return json.dumps({"status": "OK", "status_code": 200}), 200
    except Exception:
        return json.dumps({"status": "INTERNAL SERVER ERROR", "status_code": 500}), 500


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/versions")
@login_required
@user_has_access
def list_measure_versions(topic_slug, subtopic_slug, measure_slug):
    try:
        topic = page_service.get_topic(topic_slug)
        subtopic = page_service.get_subtopic(topic_slug, subtopic_slug)
        measure = page_service.get_measure(topic_slug, subtopic_slug, measure_slug)
    except PageNotFoundException:
        current_app.logger.exception(f"Measure '{topic_slug}/{subtopic_slug}/{measure_slug}' not found")
        abort(404)

    return render_template("cms/measure_versions.html", topic=topic, subtopic=subtopic, measure=measure)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/delete", methods=["GET"])
@login_required
@user_can(DELETE_MEASURE)
def confirm_delete_measure_version(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    return render_template("cms/delete_page.html", topic=topic, subtopic=subtopic, measure_version=measure_version)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/delete", methods=["POST"])
@login_required
@user_can(DELETE_MEASURE)
def delete_measure_version(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    page_service.delete_measure_version(measure_version)
    if request.referrer.endswith("/versions"):
        return redirect(
            url_for(
                "cms.list_measure_versions",
                topic_slug=topic.slug,
                subtopic_slug=subtopic.slug,
                measure_slug=measure.slug,
            )
        )
    else:
        return redirect(url_for("static_site.topic", topic_slug=topic.slug))


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/new-version", methods=["GET", "POST"])
@login_required
@user_can(CREATE_VERSION)
def new_version(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    form = NewVersionForm(measure_version)
    if form.validate_on_submit():
        version_type = form.data["version_type"]
        try:
            new_measure_version = page_service.create_measure_version(
                measure_version, NewVersionType(version_type), user=current_user
            )
            message = "Added a new %s version %s" % (version_type, new_measure_version.version)
            flash(message)
            return redirect(
                url_for(
                    "cms.edit_measure_version",
                    topic_slug=topic.slug,
                    subtopic_slug=subtopic.slug,
                    measure_slug=new_measure_version.measure.slug,
                    version=new_measure_version.version,
                )
            )
        except UpdateAlreadyExists:
            message = "Version %s of page %s is already being updated" % (version, measure_slug)
            flash(message, "error")
            return redirect(
                url_for(
                    "cms.new_version",
                    topic_slug=topic.slug,
                    subtopic_slug=subtopic.slug,
                    measure_slug=measure.slug,
                    version=measure_version.version,
                    form=form,
                )
            )

    return render_template(
        "cms/create_new_version.html",
        topic=topic,
        subtopic=subtopic,
        measure=measure,
        measure_version=measure_version,
        form=form,
        errors=get_form_errors(forms=(form,)),
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/copy", methods=["POST"])
@login_required
@user_can(COPY_MEASURE)
def copy_measure_version(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )
    copied_measure_version = page_service.create_measure_version(
        measure_version, update_type=NewVersionType.NEW_MEASURE, user=current_user
    )
    return redirect(
        url_for(
            "cms.edit_measure_version",
            topic_slug=copied_measure_version.measure.subtopic.topic.slug,
            subtopic_slug=copied_measure_version.measure.subtopic.slug,
            measure_slug=copied_measure_version.measure.slug,
            version=copied_measure_version.version,
        )
    )


@cms_blueprint.route("/set-measure-order", methods=["POST"])
@login_required
def set_measure_order():
    try:
        positions = request.json.get("positions", [])

        page_service.update_measure_position_within_subtopic(
            *[(position["measure_id"], position["subtopic_id"], position["position"]) for position in positions]
        )

        return json.dumps({"status": "OK", "status_code": 200}), 200
    except Exception as e:
        current_app.logger.exception(e)
        return json.dumps({"status": "INTERNAL SERVER ERROR", "status_code": 500}), 500


def _build_if_necessary(measure_version):
    if measure_version.eligible_for_build():
        page_service.mark_measure_version_published(measure_version)
        build_service.request_build()


@cms_blueprint.route("/measure-version/<measure_version_id>", methods=["GET"])
@login_required
def view_measure_version_by_measure_version_id(measure_version_id):
    measure_version = page_service.get_measure_version_by_id(measure_version_id)
    return redirect(
        url_for(
            "static_site.measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/edit/data-sources", methods=["GET"])
@login_required
@user_has_access
def search_data_sources(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    q = request.args.get("q", "")

    if q:
        data_sources = DataSource.search(q, limit=100)
    else:
        data_sources = None

    return render_template(
        "cms/search_data_source.html",
        topic=topic,
        subtopic=subtopic,
        measure=measure,
        measure_version=measure_version,
        q=q,
        data_sources=data_sources,
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/edit/data-sources/new", methods=["GET"])
@login_required
@user_has_access
def new_data_source(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    data_source_form = DataSourceForm()
    organisations_by_type = Organisation.select_options_by_type()

    return render_template(
        "cms/new_data_source.html",
        data_source_form=data_source_form,
        organisations_by_type=organisations_by_type,
        topic=topic,
        subtopic=subtopic,
        measure=measure,
        measure_version=measure_version,
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/edit/data-sources", methods=["POST"])
@login_required
@user_has_access
def create_data_source(topic_slug, subtopic_slug, measure_slug, version):

    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    data_source_form = DataSourceForm()

    data_source = DataSource()
    data_source_form.populate_obj(data_source)

    if data_source_form.validate_on_submit():

        db.session.add(data_source)
        measure_version.data_sources.append(data_source)
        db.session.commit()

        message = "Saved"
        flash(message, "info")

        return redirect(
            url_for(
                "cms.edit_data_source",
                topic_slug=topic.slug,
                subtopic_slug=subtopic.slug,
                measure_slug=measure.slug,
                version=measure_version.version,
                data_source_id=data_source.id,
            )
        )

    else:

        errors = get_form_errors(forms=[data_source_form])

        return render_template(
            "cms/new_data_source.html",
            data_source_form=data_source_form,
            organisations_by_type=Organisation.select_options_by_type(),
            errors=errors,
            topic=topic,
            subtopic=subtopic,
            measure=measure,
            measure_version=measure_version,
        )


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/edit/data-sources/<int:data_source_id>", methods=["GET"]
)
@login_required
@user_has_access
def edit_data_source(topic_slug, subtopic_slug, measure_slug, version, data_source_id):

    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    data_source = DataSource.query.get(data_source_id)

    if data_source is None:
        raise PageNotFoundException()

    if data_source not in measure_version.data_sources:
        raise PageNotFoundException()

    data_source_form = DataSourceForm(obj=data_source)
    organisations_by_type = Organisation.select_options_by_type()

    return render_template(
        "cms/edit_data_source.html",
        data_source=data_source,
        data_source_form=data_source_form,
        organisations_by_type=organisations_by_type,
        topic=topic,
        subtopic=subtopic,
        measure=measure,
        measure_version=measure_version,
    )


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/edit/data-sources/<int:data_source_id>", methods=["POST"]
)
@login_required
@user_has_access
def update_data_source(topic_slug, subtopic_slug, measure_slug, version, data_source_id):

    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    data_source = DataSource.query.get(data_source_id)

    if data_source is None:
        raise PageNotFoundException()

    if data_source not in measure_version.data_sources:
        raise PageNotFoundException()

    data_source_form = DataSourceForm()

    # TODO: remove check on data_source.title and validate this within form.
    if data_source_form.validate_on_submit():
        data_source_form.populate_obj(data_source)

        db.session.commit()

        message = "Saved"
        flash(message, "info")

        return redirect(
            url_for(
                "cms.edit_data_source",
                topic_slug=topic.slug,
                subtopic_slug=subtopic.slug,
                measure_slug=measure.slug,
                version=measure_version.version,
                data_source_id=data_source.id,
            )
        )

    errors = get_form_errors(forms=[data_source_form])

    return render_template(
        "cms/edit_data_source.html",
        data_source=data_source,
        data_source_form=data_source_form,
        organisations_by_type=Organisation.select_options_by_type(),
        errors=errors,
        topic=topic,
        subtopic=subtopic,
        measure=measure,
        measure_version=measure_version,
    )


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/edit/data-sources/<int:data_source_id>/remove",
    methods=["POST"],
)
@login_required
@user_has_access
def remove_data_source(topic_slug, subtopic_slug, measure_slug, version, data_source_id):
    topic, subtopic, measure, measure_version = page_service.get_measure_version_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    data_source = DataSource.query.get(data_source_id)

    if data_source is None:
        raise PageNotFoundException()

    if data_source not in measure_version.data_sources:
        raise PageNotFoundException()

    measure_version.data_sources.remove(data_source)
    db.session.commit()

    message = 'Removed data source "{}"'.format(data_source.title)
    flash(message, "error")

    return redirect(
        url_for(
            "cms.edit_measure_version",
            topic_slug=topic.slug,
            subtopic_slug=subtopic.slug,
            measure_slug=measure.slug,
            version=measure_version.version,
        )
    )
