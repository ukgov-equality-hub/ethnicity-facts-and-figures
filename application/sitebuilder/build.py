#! /usr/bin/env python
import json
import os
import shutil
import subprocess
from tempfile import NamedTemporaryFile

from bs4 import BeautifulSoup
from flask import current_app, render_template
from git import Repo
from slugify import slugify

from application.cms.data_utils import DimensionObjectBuilder
from application.cms.models import DbPage
from application.cms.page_service import page_service
from application.cms.page_utils import get_latest_subtopic_measures
from application.static_site.views import write_dimension_csv, write_dimension_tabular_csv
from application.utils import get_content_with_metadata
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

        homepage = DbPage.query.filter_by(page_type='homepage').one()
        build_from_homepage(homepage, build_dir, config=application.config)

        pages_unpublished = unpublish_pages(build_dir)

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
    topics = sorted(page.children, key=lambda t: t.title)
    out = render_template('static_site/index.html',
                          topics=topics,
                          asset_path='/static/',
                          build_timestamp=None,
                          static_mode=True)

    file_path = os.path.join(build_dir, 'index.html')
    with open(file_path, 'w') as out_file:
        out_file.write(out)

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


def write_topic_html(page, build_dir, config):

    uri = os.path.join(build_dir, page.uri)
    os.makedirs(uri, exist_ok=True)

    publication_states = config['PUBLICATION_STATES']
    json_enabled = config['JSON_ENABLED']
    local_build = config['LOCAL_BUILD']

    subtopic_measures = {}
    subtopics = _filter_out_subtopics_with_no_ready_measures(page.children, publication_states=publication_states)
    for st in subtopics:
        ms = get_latest_subtopic_measures(st, publication_states)
        subtopic_measures[st.guid] = ms

    out = render_template('static_site/topic.html',
                          page=page,
                          subtopics=subtopics,
                          asset_path='/static/',
                          static_mode=True,
                          measures=subtopic_measures)

    file_path = os.path.join(uri, 'index.html')
    with open(file_path, 'w') as out_file:
        out_file.write(out)

    for measures in subtopic_measures.values():
        for m in measures:
            write_measure_page(m, build_dir, json_enabled=json_enabled, latest=True, local_build=local_build)


def write_measure_page(page, build_dir, json_enabled=False, latest=False, local_build=False):

    uri = os.path.join(build_dir,
                       page.parent().parent().uri,
                       page.parent().uri,
                       page.uri,
                       'latest' if latest else page.version)

    os.makedirs(uri, exist_ok=True)
    versions = page_service.get_previous_major_versions(page)
    edit_history = page_service.get_previous_minor_versions(page)
    first_published_date = page_service.get_first_published_date(page)

    if not latest:
        newer_edition = page_service.get_latest_version_of_newer_edition(page)
    else:
        newer_edition = None

    dimensions = process_dimensions(page, uri, local_build)

    out = render_template('static_site/measure.html',
                          topic=page.parent().parent().uri,
                          subtopic=page.parent().uri,
                          measure_page=page,
                          dimensions=dimensions,
                          versions=versions,
                          asset_path='/static/',
                          first_published_date=first_published_date,
                          newer_edition=newer_edition,
                          edit_history=edit_history,
                          static_mode=True)

    file_path = os.path.join(uri, 'index.html')
    with open(file_path, 'w') as out_file:
        out_file.write(out)

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
        filename = page_service.get_measure_download(d, d.file_name, 'source')
        content_with_metadata = get_content_with_metadata(filename, page)
        file_path = os.path.join(download_dir, d.file_name)
        with open(file_path, 'w') as download_file:
            try:
                download_file.write(content_with_metadata)
            except Exception as e:
                message = 'Error writing download for file %s' % d.file_name
                print(message)
                print(e)


def write_measure_page_versions(versions, build_dir, json_enabled=False):
    for v in versions:
        write_measure_page(v, build_dir, json_enabled=json_enabled)


def process_dimensions(page, uri, local_build):

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
            if not local_build:
                build_chart_png(dimension=d, output_dir=chart_dir)

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
            page_dir = os.path.join(build_dir, page.parent().parent().uri, page.parent().uri, page.uri, 'latest')
            if os.path.exists(page_dir):
                shutil.rmtree(page_dir, ignore_errors=True)

    page_service.mark_pages_unpublished(pages_to_unpublish)
    return pages_to_unpublish


def build_chart_png(dimension, output_dir):
    f = NamedTemporaryFile(mode='w', delete=False)
    chart_dict = dimension.chart
    try:
        chart_dict['chart'] = {}
        chart_dict['chart']['type'] = dimension.chart['type']
        invalid_chart = False
    except KeyError:
        invalid_chart = True
    json.dump(chart_dict, f)
    f.close()
    chart_out_file = output_dir + '/%s.png' % dimension.guid
    subprocess.run(["highcharts-export-server",
                    "-infile", f.name,
                    "-outfile", chart_out_file,
                    "-width", "900"])
    os.unlink(f.name)


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
            output_path = os.path.join(output_dir, 'index.html')
            out = render_template(template_path, asset_path='/static/', static_mode=True)
            with open(output_path, 'w') as out_file:
                out_file.write(out)


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
    static_dir = '%s/static' % build_dir
    if os.path.exists(static_dir):
        shutil.rmtree(static_dir)
    shutil.copytree(current_app.static_folder, static_dir)


def _filter_out_subtopics_with_no_ready_measures(subtopics, publication_states=['APPROVED']):
    filtered = []
    for st in subtopics:
        for m in st.children:
            if m.eligible_for_build(publication_states):
                if st not in filtered:
                    filtered.append(st)
    return filtered


def _prettify(out):
    soup = BeautifulSoup(out, 'html.parser')
    return soup.prettify()


def cleanup_filename(filename):
    return slugify(filename)
