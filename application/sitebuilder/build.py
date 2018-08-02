#! /usr/bin/env python
import json
import os
import shutil
import subprocess

from flask import current_app, render_template, url_for
from git import Repo
from slugify import slugify

from application.cms.data_utils import DimensionObjectBuilder
from application.cms.models import Page
from application.cms.page_service import page_service
from application.cms.upload_service import upload_service
from application.utils import get_content_with_metadata, write_dimension_csv, write_dimension_tabular_csv
from application.cms.api_builder import build_measure_json, build_index_json


def do_it(application, build):
    with application.app_context():

        base_build_dir = application.config['STATIC_BUILD_DIR']
        os.makedirs(base_build_dir, exist_ok=True)
        build_timestamp = build.created_at.strftime('%Y%m%d_%H%M%S.%f')
        build_dir = '%s/%s_%s' % (base_build_dir, build_timestamp, build.id)
        pull_current_site(build_dir, application.config['STATIC_SITE_REMOTE_REPO'])
        delete_files_from_repo(build_dir)
        create_versioned_assets(build_dir)

        local_build = application.config['LOCAL_BUILD']

        homepage = Page.query.filter_by(page_type='homepage').one()
        build_from_homepage(homepage, build_dir, config=application.config)

        pages_unpublished = unpublish_pages(build_dir)

        build_dashboards(build_dir)

        build_other_static_pages(build_dir)

        print("Push site to git ", application.config['PUSH_SITE'])
        if application.config['PUSH_SITE']:
            push_site(build_dir, build_timestamp)

        print("Deploy site to S3 ", application.config['DEPLOY_SITE'])
        if application.config['DEPLOY_SITE']:
            from application.sitebuilder.build_service import s3_deployer
            s3_deployer(application, build_dir, deletions=pages_unpublished)

        if not local_build:
            clear_up(build_dir)


def build_from_homepage(page, build_dir, config):

    os.makedirs(build_dir, exist_ok=True)
    topics = sorted(page.children, key=lambda topic: topic.title)
    content = render_template('static_site/index.html',
                              topics=topics,
                              build_timestamp=None,
                              static_mode=True)

    file_path = os.path.join(build_dir, 'index.html')
    write_html(file_path, content)

    for topic in page.children:
        write_topic_html(topic, build_dir, config)

    json_enabled = config['JSON_ENABLED']
    if json_enabled:
        page_json_file = os.path.join(build_dir, 'data.json')
        try:
            with open(page_json_file, 'w') as out_file:
                out_file.write(json.dumps(build_index_json()))
        except Exception as e:
            print('Could not save json index file')


def write_topic_html(topic, build_dir, config):

    uri = os.path.join(build_dir, topic.uri)
    os.makedirs(uri, exist_ok=True)

    json_enabled = config['JSON_ENABLED']
    local_build = config['LOCAL_BUILD']

    subtopic_measures = {}
    subtopics = []
    for st in topic.children:
        ms = page_service.get_latest_publishable_measures(st)
        if ms:
            subtopic_measures[st.guid] = ms
            subtopics.append(st)

    content = render_template('static_site/topic.html',
                              topic=topic,
                              subtopics=subtopics,
                              static_mode=True,
                              measures=subtopic_measures)

    file_path = os.path.join(uri, 'index.html')
    write_html(file_path, content)

    for measures in subtopic_measures.values():
        for m in measures:
            write_measure_page(m, build_dir, json_enabled=json_enabled, latest=True, local_build=local_build)


def write_measure_page(page, build_dir, json_enabled=False, latest=False, local_build=False):

    uri = os.path.join(build_dir,
                       page.parent.parent.uri,
                       page.parent.uri,
                       page.uri,
                       'latest' if latest else page.version)

    os.makedirs(uri, exist_ok=True)
    versions = page_service.get_previous_major_versions(page)
    edit_history = page_service.get_previous_minor_versions(page)
    first_published_date = page_service.get_first_published_date(page)

    dimensions = process_dimensions(page, uri)

    content = render_template('static_site/measure.html',
                              topic=page.parent.parent.uri,
                              subtopic=page.parent.uri,
                              measure_page=page,
                              dimensions=dimensions,
                              versions=versions,
                              first_published_date=first_published_date,
                              edit_history=edit_history,
                              static_mode=True)

    file_path = os.path.join(uri, 'index.html')
    write_html(file_path, content)

    if json_enabled:
        page_json_file = os.path.join(uri, 'data.json')
        try:
            with open(page_json_file, 'w') as out_file:
                out_file.write(json.dumps(build_measure_json(page)))
        except Exception as e:
            print('Could not save json file %s' % page_json_file)

    if not local_build:
        write_measure_page_downloads(page, uri)

    write_measure_page_versions(versions, build_dir, json_enabled=json_enabled)


def write_measure_page_downloads(page, uri):

    if page.uploads:
        download_dir = os.path.join(uri, 'downloads')
        os.makedirs(download_dir, exist_ok=True)

    for d in page.uploads:
        try:
            filename = upload_service.get_measure_download(d, d.file_name, 'source')
            content_with_metadata = get_content_with_metadata(filename, page)
            file_path = os.path.join(download_dir, d.file_name)
            with open(file_path, 'w', encoding='windows-1252') as download_file:
                    download_file.write(content_with_metadata)
        except Exception as e:
            message = 'Error writing download for file %s' % d.file_name
            print(message)
            print(e)


def write_measure_page_versions(versions, build_dir, json_enabled=False):
    for v in versions:
        write_measure_page(v, build_dir, json_enabled=json_enabled)


def process_dimensions(page, uri):

    if page.dimensions:
        download_dir = os.path.join(uri, 'downloads')
        os.makedirs(download_dir, exist_ok=True)
    else:
        return

    dimensions = []
    for d in page.dimensions:

        if d.chart and d.chart['type'] != 'panel_bar_chart':
            chart_dir = '%s/charts' % uri
            os.makedirs(chart_dir, exist_ok=True)

        dimension_obj = DimensionObjectBuilder.build(d)
        output = write_dimension_csv(dimension=dimension_obj)

        if d.title:
            filename = '%s.csv' % cleanup_filename(d.title)
            table_filename = '%s-table.csv' % cleanup_filename(d.title)
        else:
            filename = '%s.csv' % d.guid
            table_filename = '%s-table.csv' % d.guid

        try:
            file_path = os.path.join(download_dir, filename)
            with open(file_path, 'w') as dimension_file:
                dimension_file.write(output)
        except Exception as e:
            print("Could not write file path", file_path)
            print(e)

        d_as_dict = d.to_dict()
        d_as_dict['static_file_name'] = filename

        if d.table:
            table_output = write_dimension_tabular_csv(dimension=dimension_obj)

            table_file_path = os.path.join(download_dir, table_filename)
            with open(table_file_path, 'w') as dimension_file:
                dimension_file.write(table_output)

            d_as_dict['static_table_file_name'] = table_filename

        dimensions.append(d_as_dict)

    return dimensions


def unpublish_pages(build_dir):
    pages_to_unpublish = page_service.get_pages_to_unpublish()
    for page in pages_to_unpublish:
        if page.get_previous_version() is None:
            page_dir = os.path.join(build_dir, page.parent.parent.uri, page.parent.uri, page.uri, 'latest')
            if os.path.exists(page_dir):
                shutil.rmtree(page_dir, ignore_errors=True)

    page_service.mark_pages_unpublished(pages_to_unpublish)
    return pages_to_unpublish


def build_dashboards(build_dir):
    # Import these locally, as importing at file level gives circular imports when running tests
    from application.dashboard.data_helpers import (
        get_published_dashboard_data, get_measure_progress_dashboard_data,
        get_ethnic_groups_dashboard_data, get_ethnic_group_by_uri_dashboard_data,
        get_ethnicity_categorisations_dashboard_data, get_ethnicity_categorisation_by_id_dashboard_data,
        get_geographic_breakdown_dashboard_data, get_geographic_breakdown_by_slug_dashboard_data
    )

    dashboards_dir = os.path.join(build_dir, 'dashboards')
    directories = [
        'dashboards/published', 'dashboards/measure-progress', 'dashboards/ethnic-groups',
        'dashboards/ethnicity-categorisations', 'dashboards/geographic-breakdown'
    ]
    for dir in directories:
        dir = os.path.join(build_dir, dir)
        os.makedirs(dir, exist_ok=True)

    # Dashboards home page
    content = render_template('dashboards/index.html', static_mode=True)
    file_path = os.path.join(dashboards_dir, 'index.html')
    write_html(file_path, content)

    # Published measures dashboard
    data = get_published_dashboard_data()
    content = render_template(
        'dashboards/publications.html',
        data=data,
        static_mode=True,
    )
    file_path = os.path.join(dashboards_dir, 'published/index.html')
    write_html(file_path, content)

    # Planned measures dashboard
    measures, planned_count, progress_count, review_count = get_measure_progress_dashboard_data()
    content = render_template(
        'dashboards/measure_progress.html',
        measures=measures,
        planned_count=planned_count,
        progress_count=progress_count,
        review_count=review_count,
    )
    file_path = os.path.join(dashboards_dir, 'measure-progress/index.html')
    write_html(file_path, content)

    # Ethnic groups top-level dashboard
    sorted_ethnicity_list = get_ethnic_groups_dashboard_data()
    content = render_template(
        'dashboards/ethnicity_values.html',
        ethnic_groups=sorted_ethnicity_list,
        static_mode=True,
    )
    file_path = os.path.join(dashboards_dir, 'ethnic-groups/index.html')
    write_html(file_path, content)

    # Individual ethnic group dashboards
    for ethnicity in sorted_ethnicity_list:
        slug = ethnicity['url'][ethnicity['url'].rindex('/')+1:]  # The part of the url after the final /
        value_title, page_count, results = get_ethnic_group_by_uri_dashboard_data(slug)
        content = render_template(
            'dashboards/ethnic_group.html',
            ethnic_group=value_title,
            measure_count=page_count,
            measure_tree=results,
            static_mode=True,
        )
        dir_path = os.path.join(dashboards_dir, f'ethnic-groups/{slug}')
        os.makedirs(dir_path, exist_ok=True)
        write_html(os.path.join(dir_path, "index.html"), content)

    # Ethnicity categorisations top-level dashboard
    categorisations = get_ethnicity_categorisations_dashboard_data()
    content = render_template(
        'dashboards/ethnicity_categorisations.html',
        ethnicity_categorisations=categorisations,
        static_mode=True,
    )
    file_path = os.path.join(dashboards_dir, 'ethnicity-categorisations/index.html')
    write_html(file_path, content)

    # Individual ethnicity categorisations dashboards
    for cat in categorisations:
        categorisation_title, page_count, results = get_ethnicity_categorisation_by_id_dashboard_data(cat['id'])
        content = render_template(
            'dashboards/ethnicity_categorisation.html',
            categorisation_title=categorisation_title,
            page_count=page_count,
            measure_tree=results,
            static_mode=True,
        )
        dir_path = os.path.join(dashboards_dir, f'ethnicity-categorisations/{cat["id"]}')
        os.makedirs(dir_path, exist_ok=True)
        write_html(os.path.join(dir_path, "index.html"), content)

    # Geographic breakdown top-level dashboard
    location_levels = get_geographic_breakdown_dashboard_data()
    content = render_template(
        'dashboards/geographic-breakdown.html',
        location_levels=location_levels,
        static_mode=True,
    )
    file_path = os.path.join(dashboards_dir, 'geographic-breakdown/index.html')
    write_html(file_path, content)

    # Individual geographic area dashboards
    for loc_level in location_levels:
        slug = loc_level['url'][loc_level['url'].rindex('/') + 1:]  # The part of the url after the final /
        loc, page_count, subtopics = get_geographic_breakdown_by_slug_dashboard_data(slug)
        content = render_template(
            'dashboards/lowest-level-of-geography.html',
            level_of_geography=loc.name,
            page_count=page_count,
            measure_tree=subtopics,
            static_mode=True,
        )
        dir_path = os.path.join(dashboards_dir, f'geographic-breakdown/{slug}')
        os.makedirs(dir_path, exist_ok=True)
        write_html(os.path.join(dir_path, "index.html"), content)


def build_other_static_pages(build_dir):

    template_path = os.path.join(os.getcwd(), 'application/templates/static_site/static_pages')

    for root, dirs, files in os.walk(template_path):
        for name in files:
            src_dir = root.split('/static_pages')[-1]
            if src_dir:
                if src_dir[0] == '/':
                    src_dir = src_dir[1:]
                template_path = os.path.join('static_site/static_pages', src_dir, name)
                out_dir = os.path.join(src_dir, name.replace('.html', '')).replace('_', '-')
            else:
                template_path = os.path.join('static_site/static_pages', name)
                out_dir = name.replace('.html', '').replace('_', '-')

            output_dir = os.path.join(build_dir, out_dir)
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, 'index.html')
            content = render_template(template_path, static_mode=True)
            write_html(file_path, content)


def pull_current_site(build_dir, remote_repo):
    repo = Repo.init(build_dir)
    origin = repo.create_remote('origin', remote_repo)
    origin.fetch()
    repo.create_head('master', origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
    origin.pull()


def delete_files_from_repo(build_dir):
    contents = [file for file in os.listdir(build_dir) if file not in ['.git',
                                                                       '.gitignore',
                                                                       'README.md']]
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
    message = 'Static site pushed with build timestamp %s' % build_timestamp
    repo.index.commit(message)
    repo.remotes.origin.push()
    print('static site pushed')


def clear_up(build_dir):
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)


def create_versioned_assets(build_dir):
    subprocess.run(['gulp', 'version'])
    static_dir = get_static_dir(build_dir)
    if os.path.exists(static_dir):
        shutil.rmtree(static_dir)
    shutil.copytree(current_app.static_folder, static_dir)


def write_html(file_path, content):
    with open(file_path, 'w') as out_file:
        out_file.write(content)


def cleanup_filename(filename):
    return slugify(filename)


def get_static_dir(build_dir):
    return '%s/static' % build_dir
