#! /usr/bin/env python
from datetime import datetime
import glob
import os
import shutil
import subprocess
from uuid import uuid4

from flask import current_app, render_template
from git import Repo
from slugify import slugify

from application.data.dimensions import DimensionObjectBuilder
from application.cms.models import MeasureVersion
from application.cms.page_service import page_service
from application.cms.upload_service import upload_service
from application.utils import get_csv_data_for_download, write_dimension_csv, write_dimension_tabular_csv


BUILD_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S.%f"


def make_new_build_dir(application, build=None):
    base_build_dir = application.config["STATIC_BUILD_DIR"]
    os.makedirs(base_build_dir, exist_ok=True)

    build_timestamp = _stringify_timestamp(build.created_at if build else datetime.utcnow())
    build_id = build.id if build else uuid4()

    build_dir = "%s/%s_%s" % (base_build_dir, build_timestamp, build_id)
    os.makedirs(build_dir)

    current_app.logger.info(f"New build directory: {build_dir}")

    return build_dir


def do_it(application, build):
    with application.app_context():
        print("DEBUG: do_it()")
        build_dir = make_new_build_dir(application, build=build)

        if application.config["PUSH_SITE"]:
            pull_current_site(build_dir, application.config["STATIC_SITE_REMOTE_REPO"])

        print("DEBUG do_it(): Deleting files from repo...")
        delete_files_from_repo(build_dir)
        print("DEBUG do_it(): Creating versioned assets...")
        create_versioned_assets(build_dir)

        # Inject static_mode=True into all Jinja render_template calls so that pages are automatically rendered in the
        # correct mode.
        @application.context_processor
        def enforce_static_mode():
            return dict(static_mode=True)

        local_build = application.config["LOCAL_BUILD"]

        print("DEBUG do_it(): Getting homepage...")
        homepage = MeasureVersion.query.filter_by(page_type="homepage").one()
        print("DEBUG do_it(): Building from homepage...")
        build_from_homepage(homepage, build_dir, config=application.config)

        print("DEBUG do_it(): Unpublishing pages...")
        pages_unpublished = unpublish_pages(build_dir)

        print("DEBUG do_it(): Building dashboards...")
        build_dashboards(build_dir)

        print("DEBUG do_it(): Building other static pages...")
        build_other_static_pages(build_dir)

        print(f"{'Pushing' if application.config['PUSH_SITE'] else 'NOT pushing'} site to git")
        if application.config["PUSH_SITE"]:
            push_site(build_dir, _stringify_timestamp(build.created_at))

        print(f"{'Deploying' if application.config['DEPLOY_SITE'] else 'NOT deploying'} site to S3")
        if application.config["DEPLOY_SITE"]:
            from application.sitebuilder.build_service import s3_deployer

            s3_deployer(application, build_dir, deletions=pages_unpublished)
            print("Static site deployed")

        if not local_build:
            print("DEBUG do_it(): Clearing up build directory...")
            clear_up(build_dir)


def build_and_upload_error_pages(application):
    """
    We build and upload these separately from the main site build as they go into a separate bucket and need some
    other tweaked configuration (different bucket, different directory structure on upload) that made it slightly
    convoluted and confusing to integrate into the main site build.
    """
    with application.app_context():
        build_dir = make_new_build_dir(application)

        # Inject static_mode=True into all Jinja render_template calls so that pages are automatically rendered in the
        # correct mode.
        @application.context_processor
        def enforce_static_mode():
            return dict(static_mode=True)

        local_build = application.config["LOCAL_BUILD"]

        build_error_pages(build_dir)

        print("Deploy site (error pages) to S3: ", application.config["DEPLOY_SITE"])
        if application.config["DEPLOY_SITE"]:
            from application.sitebuilder.build_service import s3_deployer, _upload_dir_to_s3
            from application.cms.file_service import S3FileSystem

            s3 = S3FileSystem(
                application.config["S3_STATIC_SITE_ERROR_PAGES_BUCKET"], region=application.config["S3_REGION"]
            )

            _upload_dir_to_s3(build_dir, s3)

        if not local_build:
            clear_up(build_dir)


def build_from_homepage(page, build_dir, config):

    os.makedirs(build_dir, exist_ok=True)
    topics = sorted(page.children, key=lambda topic: topic.title)
    content = render_template("static_site/index.html", topics=topics, build_timestamp=None)

    file_path = os.path.join(build_dir, "index.html")
    write_html(file_path, content)

    for topic in page.children:
        write_topic_html(topic, build_dir, config)


def write_topic_html(topic, build_dir, config):

    uri = os.path.join(build_dir, topic.uri)
    os.makedirs(uri, exist_ok=True)

    local_build = config["LOCAL_BUILD"]

    subtopic_measures = {}
    subtopics = []
    for st in topic.children:
        ms = page_service.get_latest_publishable_measures(st)
        if ms:
            subtopic_measures[st.guid] = ms
            subtopics.append(st)

    content = render_template("static_site/topic.html", topic=topic, subtopics=subtopics, measures=subtopic_measures)

    file_path = os.path.join(uri, "index.html")
    write_html(file_path, content)

    for measures in subtopic_measures.values():
        for m in measures:
            write_measure_page(m, build_dir, latest=True, local_build=local_build)


def write_measure_page(page, build_dir, latest=False, local_build=False):

    uri = os.path.join(
        build_dir, page.parent.parent.uri, page.parent.uri, page.uri, "latest" if latest else page.version
    )

    os.makedirs(uri, exist_ok=True)
    versions = page_service.get_previous_major_versions(page)
    edit_history = page_service.get_previous_minor_versions(page)
    first_published_date = page_service.get_first_published_date(page)

    dimensions = process_dimensions(page, uri)

    content = render_template(
        "static_site/measure.html",
        topic_uri=page.parent.parent.uri,
        subtopic_uri=page.parent.uri,
        measure_page=page,
        dimensions=dimensions,
        versions=versions,
        first_published_date=first_published_date,
        edit_history=edit_history,
    )

    file_path = os.path.join(uri, "index.html")
    write_html(file_path, content)

    if not local_build:
        write_measure_page_downloads(page, uri)

    for v in versions:
        write_measure_page(v, build_dir)


def write_measure_page_downloads(page, uri):

    if page.uploads:
        download_dir = os.path.join(uri, "downloads")
        os.makedirs(download_dir, exist_ok=True)

    for d in page.uploads:
        try:
            filename = upload_service.get_measure_download(d, d.file_name, "source")
            content = get_csv_data_for_download(filename)
            file_path = os.path.join(download_dir, d.file_name)
            with open(file_path, "w", encoding="windows-1252") as download_file:
                download_file.write(content)
        except Exception as e:
            message = "Error writing download for file %s" % d.file_name
            print(message)
            print(e)


def process_dimensions(page, uri):

    if page.dimensions:
        download_dir = os.path.join(uri, "downloads")
        os.makedirs(download_dir, exist_ok=True)
    else:
        return

    dimensions = []
    for d in page.dimensions:

        if d.chart and d.chart["type"] != "panel_bar_chart":
            chart_dir = "%s/charts" % uri
            os.makedirs(chart_dir, exist_ok=True)

        dimension_obj = DimensionObjectBuilder.build(d)
        output = write_dimension_csv(dimension=dimension_obj)

        if d.title:
            filename = "%s.csv" % cleanup_filename(d.title)
            table_filename = "%s-table.csv" % cleanup_filename(d.title)
        else:
            filename = "%s.csv" % d.guid
            table_filename = "%s-table.csv" % d.guid

        try:
            file_path = os.path.join(download_dir, filename)
            with open(file_path, "w") as dimension_file:
                dimension_file.write(output)
        except Exception as e:
            print(f"Could not write file path {file_path}")
            print(e)

        d_as_dict = d.to_dict()
        d_as_dict["static_file_name"] = filename

        if d.table:
            table_output = write_dimension_tabular_csv(dimension=dimension_obj)

            table_file_path = os.path.join(download_dir, table_filename)
            with open(table_file_path, "w") as dimension_file:
                dimension_file.write(table_output)

            d_as_dict["static_table_file_name"] = table_filename

        dimensions.append(d_as_dict)

    return dimensions


def unpublish_pages(build_dir):
    pages_to_unpublish = page_service.get_pages_to_unpublish()
    for page in pages_to_unpublish:
        if page.get_previous_version() is None:
            page_dir = os.path.join(build_dir, page.parent.parent.uri, page.parent.uri, page.uri, "latest")
            if os.path.exists(page_dir):
                shutil.rmtree(page_dir, ignore_errors=True)

    page_service.mark_pages_unpublished(pages_to_unpublish)
    return pages_to_unpublish


def build_dashboards(build_dir):
    # Import these locally, as importing at file level gives circular imports when running tests
    from application.dashboard.data_helpers import (
        get_published_dashboard_data,
        get_planned_pages_dashboard_data,
        get_ethnic_groups_dashboard_data,
        get_ethnic_group_by_uri_dashboard_data,
        get_ethnicity_classifications_dashboard_data,
        get_ethnicity_classification_by_id_dashboard_data,
        get_geographic_breakdown_dashboard_data,
        get_geographic_breakdown_by_slug_dashboard_data,
        get_published_measures_by_years_and_months,
    )

    dashboards_dir = os.path.join(build_dir, "dashboards")
    directories = [
        "dashboards/published",
        "dashboards/planned-pages",
        "dashboards/ethnic-groups",
        "dashboards/ethnicity-classifications",
        "dashboards/geographic-breakdown",
        "dashboards/whats-new",
    ]
    for dir in directories:
        dir = os.path.join(build_dir, dir)
        os.makedirs(dir, exist_ok=True)

    # Dashboards home page
    content = render_template("dashboards/index.html")
    file_path = os.path.join(dashboards_dir, "index.html")
    write_html(file_path, content)

    # New and updated pages
    pages_by_years_and_months = get_published_measures_by_years_and_months()
    content = render_template("dashboards/whats_new.html", pages_by_years_and_months=pages_by_years_and_months)
    file_path = os.path.join(dashboards_dir, "whats-new/index.html")
    write_html(file_path, content)

    # Published measures dashboard
    data = get_published_dashboard_data()
    content = render_template("dashboards/publications.html", data=data)
    file_path = os.path.join(dashboards_dir, "published/index.html")
    write_html(file_path, content)

    # Planned measures dashboard
    measures, planned_count, progress_count, review_count = get_planned_pages_dashboard_data()
    content = render_template(
        "dashboards/planned_pages.html",
        measures=measures,
        planned_count=planned_count,
        progress_count=progress_count,
        review_count=review_count,
    )
    file_path = os.path.join(dashboards_dir, "planned-pages/index.html")
    write_html(file_path, content)

    # Ethnic groups top-level dashboard
    sorted_ethnicity_list = get_ethnic_groups_dashboard_data()
    content = render_template("dashboards/ethnicity_values.html", ethnic_groups=sorted_ethnicity_list)
    file_path = os.path.join(dashboards_dir, "ethnic-groups/index.html")
    write_html(file_path, content)

    # Individual ethnic group dashboards
    for ethnicity in sorted_ethnicity_list:
        slug = ethnicity["url"][ethnicity["url"].rindex("/") + 1 :]  # The part of the url after the final /
        value_title, page_count, results = get_ethnic_group_by_uri_dashboard_data(slug)
        content = render_template(
            "dashboards/ethnic_group.html", ethnic_group=value_title, measure_count=page_count, measure_tree=results
        )
        dir_path = os.path.join(dashboards_dir, f"ethnic-groups/{slug}")
        os.makedirs(dir_path, exist_ok=True)
        write_html(os.path.join(dir_path, "index.html"), content)

    # Ethnicity classifications top-level dashboard
    classifications = get_ethnicity_classifications_dashboard_data()
    content = render_template("dashboards/ethnicity_classifications.html", ethnicity_classifications=classifications)
    file_path = os.path.join(dashboards_dir, "ethnicity-classifications/index.html")
    write_html(file_path, content)

    # Individual ethnicity classifications dashboards
    for classification in classifications:
        classification_title, page_count, results = get_ethnicity_classification_by_id_dashboard_data(
            classification["id"]
        )
        content = render_template(
            "dashboards/ethnicity_classification.html",
            classification_title=classification_title,
            page_count=page_count,
            measure_tree=results,
        )
        dir_path = os.path.join(dashboards_dir, f'ethnicity-classifications/{classification["id"]}')
        os.makedirs(dir_path, exist_ok=True)
        write_html(os.path.join(dir_path, "index.html"), content)

    # Geographic breakdown top-level dashboard
    location_levels = get_geographic_breakdown_dashboard_data()
    content = render_template("dashboards/geographic-breakdown.html", location_levels=location_levels)
    file_path = os.path.join(dashboards_dir, "geographic-breakdown/index.html")
    write_html(file_path, content)

    # Individual geographic area dashboards
    for loc_level in location_levels:
        slug = loc_level["url"][loc_level["url"].rindex("/") + 1 :]  # The part of the url after the final /
        loc, page_count, subtopics = get_geographic_breakdown_by_slug_dashboard_data(slug)
        content = render_template(
            "dashboards/lowest-level-of-geography.html",
            level_of_geography=loc.name,
            page_count=page_count,
            measure_tree=subtopics,
        )
        dir_path = os.path.join(dashboards_dir, f"geographic-breakdown/{slug}")
        os.makedirs(dir_path, exist_ok=True)
        write_html(os.path.join(dir_path, "index.html"), content)


def build_other_static_pages(build_dir):

    template_path = os.path.join(os.getcwd(), "application/templates/static_site/static_pages")

    for root, dirs, files in os.walk(template_path):
        for name in files:
            src_dir = root.split("/static_pages")[-1]
            if src_dir:
                if src_dir[0] == "/":
                    src_dir = src_dir[1:]
                template_path = os.path.join("static_site/static_pages", src_dir, name)
                out_dir = os.path.join(src_dir, name.replace(".html", "")).replace("_", "-")
            else:
                template_path = os.path.join("static_site/static_pages", name)
                out_dir = name.replace(".html", "").replace("_", "-")

            output_dir = os.path.join(build_dir, out_dir)
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, "index.html")
            content = render_template(template_path)
            write_html(file_path, content)


def build_error_pages(build_dir):
    templates_path = "application/templates"
    relative_error_pages_path = "static_site/error"
    full_error_pages_path = os.path.join(templates_path, relative_error_pages_path)

    output_dir = os.path.join(build_dir)

    for error_page_path in glob.glob(os.path.join(full_error_pages_path, "**/*.html"), recursive=True):
        # Lookup the source error file relative to the templates directory
        source_file_path = os.path.relpath(error_page_path, templates_path)

        # Save the rendered HTML with a filepath relative to its location inside `static_site/error`f
        target_file_path = os.path.relpath(error_page_path, full_error_pages_path)

        os.makedirs(os.path.join(build_dir, os.path.dirname(target_file_path)), exist_ok=True)

        error_page_html = render_template(source_file_path)
        write_html(os.path.join(output_dir, target_file_path), error_page_html)


def pull_current_site(build_dir, remote_repo):
    repo = Repo.init(build_dir)
    origin = repo.create_remote("origin", remote_repo)
    origin.fetch()
    repo.create_head("master", origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
    origin.pull()


def delete_files_from_repo(build_dir):
    contents = [file for file in os.listdir(build_dir) if file not in [".git", ".gitignore", "README.md"]]
    for file in contents:
        path = os.path.join(build_dir, file)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)


def push_site(build_dir, build_timestamp):
    repo = Repo(build_dir)
    os.chdir(build_dir)
    repo.git.add(A=True)
    message = "Static site pushed with build timestamp %s" % build_timestamp
    repo.index.commit(message)
    repo.remotes.origin.push()
    print(message)


def clear_up(build_dir):
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)


def create_versioned_assets(build_dir):
    subprocess.run(["npx", "gulp", "make"])
    static_dir = os.path.join(build_dir, get_static_dir())
    if os.path.exists(static_dir):
        shutil.rmtree(static_dir)
    shutil.copytree(current_app.static_folder, static_dir)


def write_html(file_path, content):
    with open(file_path, "w") as out_file:
        out_file.write(content)


def cleanup_filename(filename):
    return slugify(filename)


def get_static_dir():
    return "static"


def _stringify_timestamp(_timestamp):
    return _timestamp.strftime(BUILD_TIMESTAMP_FORMAT)
