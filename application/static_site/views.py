import os
from tempfile import NamedTemporaryFile

from botocore.exceptions import ClientError
from flask import render_template, abort, make_response, send_file, request

from flask_security import current_user
from flask_security import login_required
from slugify import slugify

from application.data.dimensions import DimensionObjectBuilder
from application.cms.exceptions import PageNotFoundException, DimensionNotFoundException, UploadNotFoundException
from application.cms.page_service import page_service
from application.cms.upload_service import upload_service
from application.static_site import static_site_blueprint
from application.utils import (
    get_bool,
    get_csv_data_for_download,
    write_dimension_csv,
    write_dimension_tabular_csv,
    user_has_access,
)


@static_site_blueprint.route("")
@login_required
def index():
    return render_template(
        "static_site/index.html",
        topics=page_service.get_all_topics(),
        static_mode=get_bool(request.args.get("static_mode", False)),
    )


@static_site_blueprint.route("/ethnicity-in-the-uk")
@login_required
def ethnicity_in_the_uk():
    return render_template("static_site/static_pages/ethnicity_in_the_uk.html")


@static_site_blueprint.route("/ethnicity-in-the-uk/<page_name>")
@login_required
def ethnicity_in_the_uk_page(page_name):
    ETHNICITY_IN_THE_UK_PAGES = [
        "ethnic-groups-and-data-collected",
        "ethnic-groups-by-place-of-birth",
        "ethnic-groups-by-sexual-identity",
        "ethnicity-and-type-of-family-or-household",
    ]
    if page_name in ETHNICITY_IN_THE_UK_PAGES:
        f = page_name.replace("-", "_")
        return render_template("static_site/static_pages/ethnicity_in_the_uk/%s.html" % f)
    else:
        abort(404)


@static_site_blueprint.route("/background")
@login_required
def background():
    return render_template("static_site/static_pages/background.html")


@static_site_blueprint.route("/cookies")
@login_required
def cookies():
    return render_template("static_site/static_pages/cookies.html")


@static_site_blueprint.route("/privacy-policy")
@login_required
def privacy_policy():
    return render_template("static_site/static_pages/privacy-policy.html")


@static_site_blueprint.route("/<topic_slug>")
@login_required
def topic(topic_slug):
    topic = page_service.get_topic_with_subtopics_and_measures(topic_slug)

    # We want to avoid passing measures into the template that the current user should not be able to see listed.
    # Departmental users should not be able to see unpublished measures that have not been explicitly shared with them.
    def user_can_see_measure(measure):
        if (
            any(measure_version.published for measure_version in measure.versions)
            or current_user in measure.shared_with
            or not current_user.is_departmental_user()
        ):
            return True
        else:
            return False

    subtopics = topic.subtopics
    measures_by_subtopic = {
        subtopic.id: list(filter(user_can_see_measure, subtopic.measures)) for subtopic in subtopics
    }

    return render_template(
        "static_site/topic.html",
        topic=topic,
        subtopics=subtopics,
        measures_by_subtopic=measures_by_subtopic,
        static_mode=get_bool(request.args.get("static_mode", False)),
    )


@static_site_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/export")
@login_required
@user_has_access
def measure_version_markdown(topic_slug, subtopic_slug, measure_slug, version):
    try:
        if version == "latest":
            measure_version = page_service.get_measure(topic_slug, subtopic_slug, measure_slug).latest_version
        else:
            *_, measure_version = page_service.get_measure_version_hierarchy(
                topic_slug, subtopic_slug, measure_slug, version
            )
    except PageNotFoundException:
        abort(404)
    if current_user.is_departmental_user():
        if measure_version.status not in ["DEPARTMENT_REVIEW", "APPROVED"]:
            return render_template("static_site/not_ready_for_review.html")

    dimensions = [dimension.to_dict() for dimension in measure_version.dimensions]
    return render_template(
        "static_site/export/measure_export.html",
        topic_slug=topic_slug,
        subtopic_slug=subtopic_slug,
        measure_version=measure_version,
        dimensions=dimensions,
    )


@static_site_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>")
@login_required
@user_has_access
def measure_version(topic_slug, subtopic_slug, measure_slug, version):

    try:
        if version == "latest":
            measure_version = page_service.get_measure(topic_slug, subtopic_slug, measure_slug).latest_version
        else:
            *_, measure_version = page_service.get_measure_version_hierarchy(
                topic_slug, subtopic_slug, measure_slug, version
            )
    except PageNotFoundException:
        abort(404)

    return render_template(
        "static_site/measure.html",
        topic_slug=topic_slug,
        subtopic_slug=subtopic_slug,
        measure_version=measure_version,
        dimensions=[dimension.to_dict() for dimension in measure_version.dimensions],
        versions=measure_version.previous_major_versions,
        first_published_date=measure_version.first_published_date,
        edit_history=measure_version.previous_minor_versions,
        static_mode=get_bool(request.args.get("static_mode", False)),
    )


@static_site_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/downloads/<filename>")
def measure_version_file_download(topic_slug, subtopic_slug, measure_slug, version, filename):
    try:
        *_, measure_version = page_service.get_measure_version_hierarchy(
            topic_slug, subtopic_slug, measure_slug, version
        )
        upload_obj = upload_service.get_upload(measure_version, filename)
        downloaded_file = upload_service.get_measure_download(upload_obj, filename, "source")
        content = get_csv_data_for_download(downloaded_file)
        if os.path.exists(downloaded_file):
            os.remove(downloaded_file)
        if content.strip() == "":
            abort(404)

        outfile = NamedTemporaryFile("w", encoding="windows-1252", delete=False)
        outfile.write(content)
        outfile.flush()

        return send_file(outfile.name, as_attachment=True, mimetype="text/csv", attachment_filename=filename)

    except (UploadNotFoundException, FileNotFoundError, ClientError):
        abort(404)


@static_site_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/dimension/<dimension_guid>/download"
)
def dimension_file_download(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    try:
        *_, dimension = page_service.get_measure_version_hierarchy(
            topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
        )
        dimension_obj = DimensionObjectBuilder.build(dimension)

        data = write_dimension_csv(dimension=dimension_obj)
        response = make_response(data)

        if dimension_obj["context"]["dimension"] and dimension_obj["context"]["dimension"] != "":
            filename = "%s.csv" % cleanup_filename(dimension_obj["context"]["dimension"])
        else:
            filename = "%s.csv" % cleanup_filename(dimension_obj["context"]["guid"])

        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = 'attachment; filename="%s"' % filename
        return response

    except DimensionNotFoundException:
        abort(404)


@static_site_blueprint.route(
    "/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/dimension/<dimension_guid>/tabular-download"
)
def dimension_file_table_download(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    try:
        *_, dimension = page_service.get_measure_version_hierarchy(
            topic_slug, subtopic_slug, measure_slug, version, dimension_guid=dimension_guid
        )
        dimension_obj = DimensionObjectBuilder.build(dimension)

        data = write_dimension_tabular_csv(dimension=dimension_obj)
        response = make_response(data)

        if dimension_obj["context"]["dimension"] and dimension_obj["context"]["dimension"] != "":
            filename = "%s-table.csv" % cleanup_filename(dimension_obj["context"]["dimension"].lower())
        else:
            filename = "%s-table.csv" % cleanup_filename(dimension_obj["context"]["guid"])

        response.headers["Content-Type"] = "text/csv"
        response.headers["Content-Disposition"] = 'attachment; filename="%s"' % filename
        return response

    except DimensionNotFoundException:
        abort(404)


def cleanup_filename(filename):
    return slugify(filename)


@static_site_blueprint.route("/search")
def search():
    response = make_response(
        render_template("static_site/static_pages/search.html", current_search_value=request.args.get("q", ""))
    )
    response._allow_google_custom_search_in_csp = True
    return response


@static_site_blueprint.route("/corrections")
@login_required
def corrections():
    measure_versions_corrected_and_published = page_service.get_measure_version_pairs_with_data_corrections()

    return render_template(
        "static_site/corrections.html",
        measure_versions_corrected_and_published=measure_versions_corrected_and_published,
    )
