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
from application.cms.forms import DimensionForm, DimensionRequiredForm, MeasurePageForm, NewVersionForm, UploadForm
from application.cms.models import (
    NewVersionType,
    publish_status,
    FrequencyOfRelease,
    TypeOfStatistic,
    UKCountry,
    Organisation,
    LowestLevelOfGeography,
    MeasureVersion,
    Measure,
)
from application.cms.new_page_service import new_page_service
from application.cms.page_service import page_service
from application.cms.upload_service import upload_service
from application.cms.utils import copy_form_errors, flash_message_with_form_errors, get_data_source_forms
from application.data.charts import ChartObjectDataBuilder
from application.data.standardisers.ethnicity_classification_finder import Builder2FrontendConverter
from application.data.tables import TableObjectDataBuilder
from application.sitebuilder import build_service
from application.sitebuilder.build_service import request_build
from application.utils import get_bool, user_can, user_has_access


@cms_blueprint.route("")
@login_required
def index():
    return redirect(url_for("static_site.index"))


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/measure/new", methods=["GET", "POST"])
@login_required
@user_can(CREATE_MEASURE)
def create_measure_page(topic_slug, subtopic_slug):
    try:
        topic = new_page_service.get_topic(topic_slug)
        subtopic = new_page_service.get_subtopic(topic_slug, subtopic_slug)
    except PageNotFoundException:
        abort(404)

    form = MeasurePageForm(
        frequency_choices=FrequencyOfRelease,
        type_of_statistic_choices=TypeOfStatistic,
        lowest_level_of_geography_choices=LowestLevelOfGeography,
        internal_edit_summary="Initial version",
        external_edit_summary="First published",
    )
    data_source_form, data_source_2_form = get_data_source_forms(request, measure_page=None)

    if form.validate_on_submit() and data_source_form.validate_on_submit() and data_source_2_form.validate_on_submit():
        try:
            new_measure_version = new_page_service.create_measure(
                subtopic=subtopic,
                measure_page_form=form,
                data_source_forms=(data_source_form, data_source_2_form),
                created_by_email=current_user.email,
            )

            message = "Created page {}".format(new_measure_version.title)
            flash(message, "info")
            current_app.logger.info(message)
            return redirect(
                url_for(
                    "cms.edit_measure_page",
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
                url_for("cms.create_measure_page", form=form, topic_slug=topic.slug, subtopic_slug=subtopic.slug)
            )

    return render_template(
        "cms/edit_measure_page.html",
        form=form,
        data_source_form=data_source_form,
        data_source_2_form=data_source_2_form,
        topic=topic,
        subtopic=subtopic,
        measure={},
        new=True,
        organisations_by_type=Organisation.select_options_by_type(),
        topics=new_page_service.get_all_topics(),
    )


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/uploads/<upload_guid>/delete", methods=["POST"]
)
@login_required
@user_has_access
def delete_upload(topic_slug, subtopic_slug, measure_slug, version, upload_guid):
    *_, measure_version, upload_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, upload_guid=upload_guid
    )

    upload_service.delete_upload_obj(measure_version, upload_object)

    message = "Deleted upload ‘{}’".format(upload_object.title)
    current_app.logger.info(message)
    flash(message, "info")

    return redirect(
        url_for(
            "cms.edit_measure_page",
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
    topic, subtopic, measure, measure_version, upload_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, upload_guid=upload_guid
    )

    form = UploadForm(obj=upload_object)

    if request.method == "POST":
        form = UploadForm(CombinedMultiDict((request.files, request.form)))
        if form.validate():
            f = form.upload.data if form.upload.data else None
            try:
                upload_service.edit_upload(measure=measure_version, upload=upload_object, file=f, data=form.data)
                message = "Updated upload {}".format(upload_object.title)
                flash(message, "info")
                return redirect(
                    url_for(
                        "cms.edit_measure_page",
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

    context = {"form": form, "topic": topic, "subtopic": subtopic, "measure": measure_version, "upload": upload_object}
    return render_template("cms/edit_upload.html", **context)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/delete", methods=["POST"])
@login_required
@user_has_access
def delete_dimension(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    *_, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_service.delete_dimension(measure_version, dimension_object.guid)

    message = "Deleted dimension ‘{}’".format(dimension_object.title)
    current_app.logger.info(message)
    flash(message, "info")

    return redirect(
        url_for(
            "cms.edit_measure_page",
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug,
            measure_slug=measure_slug,
            version=version,
        )
    )


def _diff_updates(form, page):
    from lxml.html.diff import htmldiff

    diffs = {}
    for k, v in form.data.items():
        if hasattr(page, k) and k != "db_version_id":
            page_value = getattr(page, k)
            if v is not None and page_value is not None:
                diff = htmldiff(str(page_value).rstrip(), str(v).rstrip())
                if "<ins>" in diff or "<del>" in diff:
                    getattr(form, k).errors.append("has been updated by %s" % page.last_updated_by)
                    diffs[k] = diff
    form.db_version_id.data = page.db_version_id
    return diffs


@cms_blueprint.route(  # noqa: C901 (complexity)
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/edit", methods=["GET", "POST"]
)
@login_required
@user_has_access
def edit_measure_page(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )
    diffs = {}

    data_source_form, data_source_2_form = get_data_source_forms(request, measure_page=measure_version)

    if measure_version.area_covered is not None:
        england = True if UKCountry.ENGLAND in measure_version.area_covered else False
        wales = True if UKCountry.WALES in measure_version.area_covered else False
        scotland = True if UKCountry.SCOTLAND in measure_version.area_covered else False
        northern_ireland = True if UKCountry.NORTHERN_IRELAND in measure_version.area_covered else False
    else:
        england = wales = scotland = northern_ireland = False

    form_kwargs = {
        "england": england,
        "wales": wales,
        "scotland": scotland,
        "northern_ireland": northern_ireland,
        "lowest_level_of_geography_choices": LowestLevelOfGeography,
    }
    if request.method == "GET":
        measure_page_form = MeasurePageForm(obj=measure_version, **form_kwargs)
    elif request.method == "POST":
        measure_page_form = MeasurePageForm(**form_kwargs)

    saved = False
    if (
        measure_page_form.validate_on_submit()
        and data_source_form.validate_on_submit()
        and data_source_2_form.validate_on_submit()
    ):
        additional_kwargs_from_request = {
            "status": request.form.get("status", None),
            "subtopic_id": request.form.get("subtopic", None),
        }
        try:
            new_page_service.update_measure_version(
                measure_version,
                measure_page_form=measure_page_form,
                data_source_forms=(data_source_form, data_source_2_form),
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
            measure_page_form.title.data = measure_version.title
        except StaleUpdateException as e:
            current_app.logger.error(e)
            diffs = _diff_updates(measure_page_form, measure_version)
            if diffs:
                flash("Your update will overwrite the latest content. Resolve the conflicts below", "error")
            else:
                flash("Your update will overwrite the latest content. Reload this page", "error")
        except PageUnEditable as e:
            current_app.logger.info(e)
            flash(str(e), "error")

    if measure_page_form.errors or data_source_form.errors or data_source_2_form.errors:
        flash_message_with_form_errors(
            lede="This page could not be saved. Please check for errors below:",
            forms=(measure_page_form, data_source_form, data_source_2_form),
        )

    current_status = measure_version.status
    available_actions = measure_version.available_actions()
    if "APPROVE" in available_actions:
        numerical_status = measure_version.publish_status(numerical=True)
        approval_state = publish_status.inv[(numerical_status + 1) % 6]

    if saved and "save-and-review" in request.form:
        return redirect(
            url_for(
                "cms.send_to_review",
                topic_slug=measure_version.measure.subtopic.topic.slug,
                subtopic_slug=measure_version.measure.subtopic.slug,
                measure_slug=measure_version.measure.slug,
                version=measure_version.version,
            )
        )
    elif saved:
        return redirect(
            url_for(
                "cms.edit_measure_page",
                topic_slug=measure_version.measure.subtopic.topic.slug,
                subtopic_slug=measure_version.measure.subtopic.slug,
                measure_slug=measure_version.measure.slug,
                version=measure_version.version,
            )
        )
    context = {
        "form": measure_page_form,
        "topic": measure_version.measure.subtopic.topic,
        "subtopic": measure_version.measure.subtopic,
        "measure": measure_version,
        "data_source_form": data_source_form,
        "data_source_2_form": data_source_2_form,
        "status": current_status,
        "available_actions": available_actions,
        "next_approval_state": approval_state if "APPROVE" in available_actions else None,
        "diffs": diffs,
        "organisations_by_type": Organisation.select_options_by_type(),
        "topics": new_page_service.get_all_topics(),
    }

    return render_template("cms/edit_measure_page.html", **context)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/upload", methods=["GET", "POST"])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_upload(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    form = UploadForm()
    if request.method == "POST":
        form = UploadForm(CombinedMultiDict((request.files, request.form)))
        if form.validate():
            f = form.upload.data
            try:
                upload = upload_service.create_upload(
                    page=measure_version, upload=f, title=form.data["title"], description=form.data["description"]
                )

                message = 'Uploaded file "{}" to measure "{}"'.format(upload.title, measure_slug)
                current_app.logger.info(message)
                flash(message, "info")

            except (UploadCheckError, UploadAlreadyExists) as e:
                message = "Error uploading file. {}".format(str(e))
                current_app.logger.exception(e)
                flash(message, "error")
                context = {"form": form, "topic": topic, "subtopic": subtopic, "measure": measure_version}
                return render_template("cms/create_upload.html", **context)

            return redirect(
                url_for(
                    "cms.edit_measure_page",
                    topic_slug=topic.slug,
                    subtopic_slug=subtopic.slug,
                    measure_slug=measure.slug,
                    version=measure_version.version,
                )
            )

    context = {"form": form, "topic": topic, "subtopic": subtopic, "measure": measure_version}
    return render_template("cms/create_upload.html", **context)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/send-to-review", methods=["GET"])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def send_to_review(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    # in case user tries to directly GET this page
    if measure_version.status == "DEPARTMENT_REVIEW":
        abort(400)

    if measure_version.area_covered is not None:
        england = True if UKCountry.ENGLAND in measure_version.area_covered else False
        wales = True if UKCountry.WALES in measure_version.area_covered else False
        scotland = True if UKCountry.SCOTLAND in measure_version.area_covered else False
        northern_ireland = True if UKCountry.NORTHERN_IRELAND in measure_version.area_covered else False
    else:
        england = wales = scotland = northern_ireland = False

    measure_page_form_to_validate = MeasurePageForm(
        obj=measure_version,
        meta={"csrf": False},
        england=england,
        wales=wales,
        scotland=scotland,
        northern_ireland=northern_ireland,
        lowest_level_of_geography_choices=LowestLevelOfGeography,
        sending_to_review=True,
    )

    data_source_form_to_validate, data_source_2_form_to_validate = get_data_source_forms(
        request, measure_page=measure_version, sending_to_review=True
    )

    invalid_dimensions = []

    for dimension in measure_version.dimensions:
        dimension_form = DimensionRequiredForm(obj=dimension, meta={"csrf": False})
        if not dimension_form.validate():
            invalid_dimensions.append(dimension)

    measure_page_form_validated = measure_page_form_to_validate.validate()
    data_source_form_validated = data_source_form_to_validate.validate()

    # We only want to validate the secondary source if some data has been provided, in which case we ensure that the
    # full data source is given.
    data_source_2_form_validated = (
        data_source_2_form_to_validate.validate() if any(data_source_2_form_to_validate.data.values()) else True
    )

    if (
        not measure_page_form_validated
        or invalid_dimensions
        or not data_source_form_validated
        or not data_source_2_form_validated
    ):
        # don't need to show user page has been saved when
        # required field validation failed.
        session.pop("_flashes", None)

        # Recreate form with csrf token for next update
        measure_page_form = MeasurePageForm(
            obj=measure_version,
            england=england,
            wales=wales,
            scotland=scotland,
            northern_ireland=northern_ireland,
            lowest_level_of_geography_choices=LowestLevelOfGeography,
        )

        data_source_form, data_source_2_form = get_data_source_forms(request, measure_page=measure_version)

        copy_form_errors(from_form=measure_page_form_to_validate, to_form=measure_page_form)
        copy_form_errors(from_form=data_source_form_to_validate, to_form=data_source_form)
        copy_form_errors(from_form=data_source_2_form_to_validate, to_form=data_source_2_form)

        flash_message_with_form_errors(
            lede="Cannot submit for review, please see errors below:",
            forms=(measure_page_form, data_source_form, data_source_2_form),
        )

        if invalid_dimensions:
            for invalid_dimension in invalid_dimensions:
                message = (
                    "Cannot submit for review "
                    '<a href="./%s/edit?validate=true">%s</a> dimension is not complete.'
                    % (invalid_dimension.guid, invalid_dimension.title)
                )
                flash(message, "dimension-error")

        current_status = measure_version.status
        available_actions = measure_version.available_actions()
        if "APPROVE" in available_actions:
            numerical_status = measure_version.publish_status(numerical=True)
            approval_state = publish_status.inv[numerical_status + 1]

        context = {
            "form": measure_page_form,
            "data_source_form": data_source_form,
            "data_source_2_form": data_source_2_form,
            "topic": topic,
            "subtopic": subtopic,
            "measure": measure_version,
            "status": current_status,
            "available_actions": available_actions,
            "next_approval_state": approval_state if "APPROVE" in available_actions else None,
            "organisations_by_type": Organisation.select_options_by_type(),
            "topics": new_page_service.get_all_topics(),
        }

        return render_template("cms/edit_measure_page.html", **context)

    message = page_service.next_state(measure_version, updated_by=current_user.email)
    current_app.logger.info(message)
    flash(message, "info")

    return redirect(
        url_for(
            "cms.edit_measure_page",
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug,
            measure_slug=measure_slug,
            version=version,
        )
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/publish", methods=["GET"])
@login_required
@user_has_access
@user_can(PUBLISH)
def publish(topic_slug, subtopic_slug, measure_slug, version):
    *_, measure_version = new_page_service.get_measure_page_hierarchy(topic_slug, subtopic_slug, measure_slug, version)

    if measure_version.status != "DEPARTMENT_REVIEW":
        abort(400)

    message = page_service.next_state(measure_version, current_user.email)
    current_app.logger.info(message)
    _build_if_necessary(measure_version)
    flash(message, "info")
    return redirect(
        url_for(
            "cms.edit_measure_page",
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug,
            measure_slug=measure_slug,
            version=version,
        )
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/reject")
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def reject_page(topic_slug, subtopic_slug, measure_slug, version):
    *_, measure_version = new_page_service.get_measure_page_hierarchy(topic_slug, subtopic_slug, measure_slug, version)

    # Can only reject if currently under review
    if measure_version.status not in {"INTERNAL_REVIEW", "DEPARTMENT_REVIEW"}:
        abort(400)

    message = new_page_service.reject_measure_version(measure_version)
    flash(message, "info")
    current_app.logger.info(message)
    return redirect(
        url_for(
            "cms.edit_measure_page",
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug,
            measure_slug=measure_slug,
            version=version,
        )
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/unpublish")
@login_required
@user_has_access
@user_can(PUBLISH)
def unpublish_page(topic_slug, subtopic_slug, measure_slug, version):
    *_, measure_version = new_page_service.get_measure_page_hierarchy(topic_slug, subtopic_slug, measure_slug, version)

    # Can only unpublish if currently published
    if measure_version.status != "APPROVED":
        abort(400)

    message = new_page_service.unpublish_measure_version(measure_version, unpublished_by=current_user.email)
    _build_if_necessary(measure_version)
    flash(message, "info")
    current_app.logger.info(message)
    return redirect(
        url_for(
            "cms.edit_measure_page",
            topic_slug=topic_slug,
            subtopic_slug=subtopic_slug,
            measure_slug=measure_slug,
            version=version,
        )
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/draft")
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def send_page_to_draft(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    message = new_page_service.send_measure_version_to_draft(measure_version)
    flash(message, "info")
    current_app.logger.info(message)
    return redirect(
        url_for(
            "cms.edit_measure_page",
            topic_slug=topic.slug,
            subtopic_slug=subtopic.slug,
            measure_slug=measure.slug,
            version=measure_version.version,
        )
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/dimension/new", methods=["GET", "POST"])
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_dimension(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    if request.method == "POST":
        return _post_create_dimension(topic.slug, subtopic.slug, measure.slug, measure_version.version)
    else:
        return _get_create_dimension(topic.slug, subtopic.slug, measure.slug, measure_version.version)


def _post_create_dimension(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )
    form = DimensionForm(request.form)

    if form.validate():
        try:
            dimension = dimension_service.create_dimension(
                page=measure_version,
                title=form.data["title"],
                time_period=form.data["time_period"],
                summary=form.data["summary"],
                # ethnicity_classification_id=form.data["ethnicity_classification"],
                # include_parents=form.data["include_parents"],
                # include_all=form.data["include_all"],
                # include_unknown=form.data["include_unknown"],
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
    else:
        flash("Please complete all fields in the form", "error")
        return _get_create_dimension(topic_slug, subtopic_slug, measure_slug, version, form=form)


def _get_create_dimension(topic, subtopic, measure, version, form=None):
    if form is None:
        context_form = DimensionForm()
    else:
        context_form = form

    topic, subtopic, measure, measure_version = new_page_service.get_measure_page_hierarchy(
        topic, subtopic, measure, version
    )

    context = {"form": context_form, "create": True, "topic": topic, "subtopic": subtopic, "measure": measure_version}
    return render_template("cms/create_dimension.html", **context)


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
    topic, subtopic, measure, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
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
    topic, subtopic, measure, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_classification = dimension_object.dimension_classification

    if form is None:
        form = DimensionForm(obj=dimension_object)

    context = {
        "form": form,
        "topic": topic,
        "subtopic": subtopic,
        "measure": measure_version,
        "dimension": dimension_object,
        "ethnicity_classification": dimension_classification.classification.long_title
        if dimension_classification
        else None,
        "includes_all": dimension_classification.includes_all if dimension_classification else None,
        "includes_parents": dimension_classification.includes_parents if dimension_classification else None,
        "includes_unknown": dimension_classification.includes_unknown if dimension_classification else None,
        "classification_source": dimension_object.classification_source_string,
    }

    return render_template("cms/edit_dimension.html", **context)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/chartbuilder")
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def chartbuilder(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    topic, subtopic, measure, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_dict = dimension_object.to_dict()

    if "chart_builder_version" in dimension_dict and dimension_dict["chart_builder_version"] == 1:
        return redirect(
            url_for(
                "cms.create_chart_original",
                topic_slug=topic.slug,
                subtopic_slug=subtopic.slug,
                measure_slug=measure.slug,
                version=measure_version.version,
                dimension_guid=dimension_object.guid,
            )
        )

    return redirect(
        url_for(
            "cms.create_chart",
            topic_slug=topic.slug,
            subtopic_slug=subtopic.slug,
            measure_slug=measure.slug,
            version=measure_version.version,
            dimension_guid=dimension_object.guid,
        )
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/create-chart")
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_chart(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    topic, subtopic, measure, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_dict = dimension_object.to_dict()

    if dimension_dict["chart_source_data"] is not None and dimension_dict["chart_2_source_data"] is None:
        dimension_dict["chart_2_source_data"] = ChartObjectDataBuilder.upgrade_v1_to_v2(
            dimension_dict["chart"], dimension_dict["chart_source_data"]
        )

    context = {
        "topic": topic,
        "subtopic": subtopic,
        "measure": measure_version,
        "dimension": dimension_dict,
        "classification_options": __get_classification_finder_classifications(),
    }

    return render_template("cms/create_chart_2.html", **context)


def __get_classification_finder_classifications():
    classification_collection = current_app.classification_finder.get_classification_collection()
    classifications = classification_collection.get_sorted_classifications()
    return [{"code": classification.get_id(), "name": classification.get_name()} for classification in classifications]


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/create-chart/advanced")
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_chart_original(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    topic, subtopic, measure, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    context = {
        "topic": topic,
        "subtopic": subtopic,
        "measure": measure_version,
        "dimension": dimension_object.to_dict(),
    }

    return render_template("cms/create_chart.html", **context)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/tablebuilder")
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def tablebuilder(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    topic, subtopic, measure, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_dict = dimension_object.to_dict()

    if "table_builder_version" in dimension_dict and dimension_dict["table_builder_version"] == 1:
        return redirect(
            url_for(
                "cms.create_table_original",
                topic_slug=topic.slug,
                subtopic_slug=subtopic.slug,
                measure_slug=measure.slug,
                version=measure_version.version,
                dimension_guid=dimension_object.guid,
            )
        )

    return redirect(
        url_for(
            "cms.create_table",
            topic_slug=topic.slug,
            subtopic_slug=subtopic.slug,
            measure_slug=measure.slug,
            version=measure_version.version,
            dimension_guid=dimension_object.guid,
        )
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/create-table/advanced")
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_table_original(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    topic, subtopic, measure, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    context = {
        "topic": topic,
        "subtopic": subtopic,
        "measure": measure_version,
        "dimension": dimension_object.to_dict(),
    }

    return render_template("cms/create_table.html", **context)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/create-table")
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def create_table(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    topic, subtopic, measure, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_dict = dimension_object.to_dict()

    # migration step
    if dimension_dict["table_source_data"] is not None and dimension_dict["table_2_source_data"] is None:
        dimension_dict["table_2_source_data"] = TableObjectDataBuilder.upgrade_v1_to_v2(
            dimension_dict["table"], dimension_dict["table_source_data"], current_app.dictionary_lookup
        )

    context = {
        "topic": topic,
        "subtopic": subtopic,
        "measure": measure_version,
        "dimension": dimension_dict,
        "classification_options": __get_classification_finder_classifications(),
    }

    return render_template("cms/create_table_2.html", **context)


@cms_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/save-chart", methods=["POST"]
)
@login_required
@user_has_access
@user_can(UPDATE_MEASURE)
def save_chart_to_page(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    *_, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    if measure_version.not_editable():
        message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(measure_version.guid)
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
    *_, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_object.delete_chart()

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
    *_, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    if measure_version.not_editable():
        message = 'Error updating page "{}" - only pages in DRAFT or REJECT can be edited'.format(measure_version.guid)
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
    *_, measure_version, dimension_object = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
    )

    dimension_object.delete_table()

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
def get_measure_page_uploads(topic_slug, subtopic_slug, measure_slug, version):
    *_, measure_version = new_page_service.get_measure_page_hierarchy(topic_slug, subtopic_slug, measure_slug, version)

    uploads = upload_service.get_page_uploads(measure_version) or {}
    return json.dumps({"uploads": uploads}), 200


def _build_is_required(page, req, beta_publication_states):
    if page.status == "UNPUBLISH":
        return True
    if get_bool(req.args.get("build")) and page.eligible_for_build(beta_publication_states):
        return True
    return False


@cms_blueprint.route("/data-processor", methods=["POST"])
@login_required
def process_input_data():
    if current_app.dictionary_lookup:
        request_json = request.json
        return_data = current_app.dictionary_lookup.process_data(request_json["data"])
        return json.dumps({"data": return_data}), 200
    else:
        return json.dumps(request.json), 200


@cms_blueprint.route("/get-valid-classifications-for-data", methods=["POST"])
@login_required
def get_valid_classifications():
    """
    This is an AJAX endpoint for the EthnicityClassificationFinder data standardiser

    It is called whenever data needs to be cleaned up for use in second generation front end data tools
    (chartbuilder 2 & potentially tablebuilder 2)

    :return: A list of processed versions of input data using different "classifications"
    """
    request_data = request.json["data"]
    valid_classifications_data = current_app.classification_finder.find_classifications(request_data)

    return_data = Builder2FrontendConverter(valid_classifications_data).convert_to_builder2_format()
    return json.dumps({"presets": return_data}), 200


# TODO: Figure out if this endpoint really needs to take topic/subtopic/measure?
# * If so, it should also take version and call page_service.get_measure_page_hierarchy
# * If not, refactor to remove these parameters from the url and call signature
@cms_blueprint.route("/<topic>/<subtopic>/<measure>/set-dimension-order", methods=["POST"])
@login_required
def set_dimension_order(topic, subtopic, measure):
    dimensions = request.json.get("dimensions", [])
    try:
        dimension_service.set_dimension_positions(dimensions)
        return json.dumps({"status": "OK", "status_code": 200}), 200
    except Exception:
        return json.dumps({"status": "INTERNAL SERVER ERROR", "status_code": 500}), 500


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/versions")
@login_required
@user_has_access
def list_measure_page_versions(topic_slug, subtopic_slug, measure_slug):
    try:
        topic = new_page_service.get_topic(topic_slug)
        subtopic = new_page_service.get_subtopic(topic_slug, subtopic_slug)
        measure = new_page_service.get_measure(topic_slug, subtopic_slug, measure_slug)
    except PageNotFoundException:
        current_app.logger.exception(f"Measure '{topic_slug}/{subtopic_slug}/{measure_slug}' not found")
        abort(404)

    return render_template("cms/measure_page_versions.html", topic=topic, subtopic=subtopic, measure=measure)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/delete", methods=["GET"])
@login_required
@user_can(DELETE_MEASURE)
def confirm_delete_measure_page(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    return render_template("cms/delete_page.html", topic=topic, subtopic=subtopic, measure_page=measure_version)


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/delete", methods=["POST"])
@login_required
@user_can(DELETE_MEASURE)
def delete_measure_page(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    page_service.delete_measure_page(measure_version.guid, version)
    if request.referrer.endswith("/versions"):
        return redirect(
            url_for(
                "cms.list_measure_page_versions",
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
    topic, subtopic, measure, measure_version = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )

    form = NewVersionForm()
    if form.validate_on_submit():
        version_type = form.data["version_type"]
        try:
            new_measure_version = page_service.create_copy(
                measure_version.guid,
                measure_version.version,
                NewVersionType(version_type),
                created_by=current_user.email,
            )
            message = "Added a new %s version %s" % (version_type, new_measure_version.version)
            flash(message)
            return redirect(
                url_for(
                    "cms.edit_measure_page",
                    topic_slug=topic.slug,
                    subtopic_slug=subtopic.slug,
                    measure_slug=new_measure_version.slug,
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
        "cms/create_new_version.html", topic=topic, subtopic=subtopic, measure=measure_version, form=form
    )


@cms_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/copy", methods=["POST"])
@login_required
@user_can(COPY_MEASURE)
def copy_measure_page(topic_slug, subtopic_slug, measure_slug, version):
    topic, subtopic, measure, measure_version = new_page_service.get_measure_page_hierarchy(
        topic_slug, subtopic_slug, measure_slug, version
    )
    copied_measure_version = new_page_service.create_measure_version(
        measure_version, update_type=NewVersionType.NEW_MEASURE, user=current_user
    )
    return redirect(
        url_for(
            "cms.edit_measure_page",
            topic_slug=copied_measure_version.measure.subtopic.topic.slug,
            subtopic_slug=copied_measure_version.measure.subtopic.slug,
            measure_slug=copied_measure_version.measure.slug,
            version=copied_measure_version.version,
        )
    )


@cms_blueprint.route("/set-measure-order", methods=["POST"])
@login_required
def set_measure_order():
    from application import db

    try:
        positions = request.json.get("positions", [])
        for p in positions:
            pages = MeasureVersion.query.filter_by(guid=p["guid"], parent_guid=p["subtopic"]).all()
            for page in pages:
                page.position = p["position"]

            if pages:
                measure = Measure.query.get(pages[0].measure_id)
                measure.position = p["position"]

        db.session.commit()
        request_build()
        return json.dumps({"status": "OK", "status_code": 200}), 200
    except Exception as e:
        current_app.logger.exception(e)
        return json.dumps({"status": "INTERNAL SERVER ERROR", "status_code": 500}), 500


def _build_if_necessary(page):
    if page.status == "UNPUBLISH":
        build_service.request_build()
    elif page.eligible_for_build():
        page_service.mark_page_published(page)
        build_service.request_build()
