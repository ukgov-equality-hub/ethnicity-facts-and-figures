import os

from tempfile import NamedTemporaryFile

from botocore.exceptions import ClientError
from flask import render_template, abort, make_response, send_file, request

from flask_security import current_user
from flask_security import login_required

from application.data.dimensions import DimensionObjectBuilder
from application.cms.exceptions import PageNotFoundException, DimensionNotFoundException, UploadNotFoundException
from application.cms.page_service import page_service
from application.cms.upload_service import upload_service
from application.static_site import static_site_blueprint
from application.utils import (
    get_csv_data_for_download,
    write_dimension_csv,
    write_dimension_tabular_csv,
    user_has_access,
)
from application.utils import cleanup_filename


@static_site_blueprint.route("")
@login_required
def index():
    return render_template("static_site/index.html", topics=page_service.get_topics(include_testing_space=False))


@static_site_blueprint.route("/ethnicity-in-the-uk/<page_name>")
@login_required
def ethnicity_in_the_uk_page(page_name):
    if page_name.lower() in {"ethnic-groups-by-sexual-identity"}:
        f = page_name.replace("-", "_")
        return render_template("static_site/static_pages/ethnicity_in_the_uk/%s.html" % f)
    else:
        abort(404)


@static_site_blueprint.route("/background")
@login_required
def background():
    return render_template("static_site/static_pages/background.html")


@static_site_blueprint.route("/cookies")
def cookies():
    return render_template("static_site/static_pages/cookies.html")


@static_site_blueprint.route("/cookie-settings")
def cookie_settings():
    return render_template("static_site/static_pages/cookie-settings.html")


@static_site_blueprint.route("/privacy-policy")
@login_required
def privacy_policy():
    return render_template("static_site/static_pages/privacy-policy.html")


@static_site_blueprint.route("/<topic_slug>")
@login_required
def topic(topic_slug):
    topic = page_service.get_topic_with_subtopics_and_measures(topic_slug)

    # We want to avoid passing measures into the template that the current user should not be able to see listed.
    def user_can_see_measure(measure):
        if (
            any(
                (measure_version.status == "APPROVED" and measure_version.published_at is not None)
                for measure_version in measure.versions
            )
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
        "static_site/topic.html", topic=topic, subtopics=subtopics, measures_by_subtopic=measures_by_subtopic
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

    return render_template(
        "static_site/export/measure_export.html",
        topic_slug=topic_slug,
        subtopic_slug=subtopic_slug,
        measure_version=measure_version,
    )


@static_site_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>")
@login_required
def measure_version(topic_slug, subtopic_slug, measure_slug, version):

    measure = page_service.get_measure(topic_slug, subtopic_slug, measure_slug)

    try:
        if version == "latest":

            latest_url = True
            if current_user.can_access_measure(measure):
                measure_version = measure.latest_version
            else:
                measure_version = measure.latest_published_version

        else:
            latest_url = False
            *_, measure_version = page_service.get_measure_version_hierarchy(
                topic_slug, subtopic_slug, measure_slug, version
            )

            if not (current_user.can_access_measure(measure) or measure_version.status == "APPROVED"):
                abort(403)

    except PageNotFoundException:
        abort(404)

    return render_template(
        "static_site/measure.html",
        topic_slug=topic_slug,
        subtopic_slug=subtopic_slug,
        measure_version=measure_version,
        latest_url=latest_url,
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
    measure_versions_with_corrections = page_service.get_measure_versions_with_data_corrections()

    return render_template(
        "static_site/corrections.html", measure_versions_with_corrections=measure_versions_with_corrections
    )


@static_site_blueprint.route("/understanding-our-data")
def understanding_our_data():
    return render_template("static_site/static_pages/understanding_our_data.html")


@static_site_blueprint.route("/understanding-our-data/how-to-read-survey-data")
def how_to_read_survey_data():
    return render_template("static_site/static_pages/understanding_our_data/how_to_read_survey_data.html")


@static_site_blueprint.route("/understanding-our-data/interpreting-our-data")
def interpreting_our_data():
    return render_template("static_site/static_pages/understanding_our_data/interpreting_our_data.html")


@static_site_blueprint.route("/understanding-our-data/how-we-use-census-data")
def how_we_use_census_data():
    return render_template("static_site/static_pages/understanding_our_data/how_we_use_census_data.html")


@static_site_blueprint.route("/understanding-our-data/our-statistical-principles")
def our_statistical_principles():
    return render_template("static_site/static_pages/understanding_our_data/our_statistical_principles.html")


# summaries
@static_site_blueprint.route("/summaries/indian-ethnic-group")
def indian_ethnic_group():
    return render_template("static_site/static_pages/summaries/indian_ethnic_group.html")


@static_site_blueprint.route("/summaries/chinese-ethnic-group")
def chinese_ethnic_group():
    return render_template("static_site/static_pages/summaries/chinese_ethnic_group.html")


@static_site_blueprint.route("/summaries/black-caribbean-ethnic-group")
def black_caribbean_ethnic_group():
    return render_template("static_site/static_pages/summaries/black_caribbean_ethnic_group.html")


@static_site_blueprint.route("/summaries/public-sector-workforces")
def public_sector_workforces():
    return render_template("static_site/static_pages/summaries/public_sector_workforces.html")


# style guide
@static_site_blueprint.route("/style-guide")
def style_guide():
    return render_template("static_site/static_pages/style_guide.html")


@static_site_blueprint.route("/style-guide/principles")
def style_guide_principles():
    return render_template("static_site/static_pages/style_guide/principles.html")


@static_site_blueprint.route("/style-guide/writing-about-ethnicity")
def style_guide_writing_about_ethnicity():
    return render_template("static_site/static_pages/style_guide/writing_about_ethnicity.html")


@static_site_blueprint.route("/style-guide/a-z")
def style_guide_a_z():
    return render_template("static_site/static_pages/style_guide/a_z.html")


@static_site_blueprint.route("/style-guide/ethnic-groups")
@login_required
def style_guide_ethnic_groups():
    return render_template("static_site/static_pages/style_guide/ethnic_groups.html")
