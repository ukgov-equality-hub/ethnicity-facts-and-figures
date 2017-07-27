#! /usr/bin/env python
import json
import os
import shutil
from datetime import datetime

from bs4 import BeautifulSoup
from flask import current_app, render_template
from git import Repo

from application.cms.page_service import page_service
from application.static_site.views import write_dimension_csv


def do_it(application):
    with application.app_context():
        base_build_dir = application.config['BUILD_DIR']
        application_url = application.config['RDU_SITE']
        if not os.path.isdir(base_build_dir):
            os.mkdir(base_build_dir)
        build_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S.%f')
        beta_publication_states = application.config['BETA_PUBLICATION_STATES']

        build_dir = '%s/%s' % (base_build_dir, build_timestamp)
        pull_current_site(build_dir, application.config['STATIC_SITE_REMOTE_REPO'])
        from application.cms.page_service import page_service
        static_dir = '%s/static' % build_dir
        if os.path.exists(static_dir):
            shutil.rmtree(static_dir)
        shutil.copytree(current_app.static_folder, static_dir)
        topics = page_service.get_topics()
        build_homepage(topics, build_dir, build_timestamp=build_timestamp)
        for topic in topics:
            topic_dir = '%s/%s' % (build_dir, topic.uri)
            if not os.path.exists(topic_dir):
                os.mkdir(topic_dir)

            subtopics = _filter_if_no_ready_measures(topic.children, beta_publication_states)
            subtopics = _order_subtopics(topic, subtopics)
            build_subtopic_pages(subtopics, topic, topic_dir)
            build_measure_pages(page_service, subtopics, topic, topic_dir, beta_publication_states, application_url)

        build_other_static_pages(build_dir)

        if application.config['ENVIRONMENT'] == 'PRODUCTION':
            push_site(build_dir, build_timestamp)
            clear_up(build_dir)


def build_subtopic_pages(subtopics, topic, topic_dir):
    approval_states = current_app.config['BETA_PUBLICATION_STATES']
    out = render_template('static_site/topic.html',
                          page=topic,
                          subtopics=subtopics,
                          asset_path='/static/',
                          static_mode=True,
                          approval_states=approval_states)

    file_path = '%s/index.html' % topic_dir
    with open(file_path, 'w') as out_file:
        out_file.write(_prettify(out))


def build_measure_pages(page_service, subtopics, topic, topic_dir, beta_publication_states, application_url):
    for st in subtopics:
        for measure_page in st.children:
            if measure_page.eligible_for_build(beta_publication_states):
                measure_dir = '%s/%s/%s/latest' % (topic_dir, st.uri, measure_page.uri)
                if not os.path.exists(measure_dir):
                    os.makedirs(measure_dir)

                if not os.path.exists(measure_dir):
                    os.makedirs(measure_dir)

                download_dir = '%s/downloads' % measure_dir
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)

                measure_html_file = '%s/index.html' % measure_dir
                measure_json_file = '%s/data.json' % measure_dir

                dimensions = []
                for d in measure_page.dimensions:
                    output = write_dimension_csv(d, application_url)
                    if d.title:
                        filename = '%s.csv' % d.title.lower().strip().replace(' ', '_').replace(',', '')
                    else:
                        filename = '%s.csv' % d.guid

                    file_path = os.path.join(download_dir, filename)
                    with open(file_path, 'w') as dimension_file:
                        dimension_file.write(output)

                    d_as_dict = d.to_dict()
                    d_as_dict['static_file_name'] = filename
                    dimensions.append(d_as_dict)

                write_measure_page_downloads(measure_page, download_dir)

                out = render_template('static_site/measure.html',
                                      topic=topic.uri,
                                      measure_page=measure_page,
                                      dimensions=dimensions,
                                      asset_path='/static/',
                                      static_mode=True)

                with open(measure_html_file, 'w') as out_file:
                    out_file.write(_prettify(out))

                with open(measure_json_file, 'w') as out_file:
                    out_file.write(json.dumps(measure_page.to_dict()))
                page_service.mark_page_published(measure_page)


def build_homepage(topics, site_dir, build_timestamp=None):
    out = render_template('static_site/index.html',
                          topics=topics,
                          asset_path='/static/',
                          build_timestamp=build_timestamp,
                          static_mode=True)

    file_path = '%s/index.html' % site_dir
    with open(file_path, 'w') as out_file:
        out_file.write(_prettify(out))


def build_other_static_pages(build_dir):
    out = render_template('static_site/about_ethnicity.html', asset_path='/static/', static_mode=True)
    file_path = '%s/about-ethnicity.html' % build_dir
    with open(file_path, 'w') as out_file:
        out_file.write(_prettify(out))

    out = render_template('static_site/ethnic_groups_and_data_collected.html', asset_path='/static/', static_mode=True)
    file_path = '%s/ethnic-groups-and-data-collected.html' % build_dir
    with open(file_path, 'w') as out_file:
        out_file.write(_prettify(out))

    out = render_template('static_site/background.html', asset_path='/static/', static_mode=True)
    file_path = '%s/background.html' % build_dir
    with open(file_path, 'w') as out_file:
        out_file.write(_prettify(out))


def write_measure_page_downloads(measure_page, download_dir):
    downloads = measure_page.uploads
    for d in downloads:
        file_contents = page_service.get_measure_download(d, d.file_name, 'data')
        file_path = os.path.join(download_dir, d.file_name)
        with open(file_path, 'w') as download_file:
            download_file.write(file_contents.decode('utf-8'))


def pull_current_site(build_dir, remote_repo):
    repo = Repo.init(build_dir)
    origin = repo.create_remote('origin', remote_repo)
    origin.fetch()
    repo.create_head('master', origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
    origin.pull()
    contents = [file for file in os.listdir(build_dir) if file not in ['.git', '.htpasswd', '.htaccess', 'index.php']]
    for file in contents:
        path = os.path.join(build_dir, file)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)


def push_site(build_dir, build_timestamp):
    repo = Repo(build_dir)
    os.chdir(build_dir)
    files = [file for file in os.listdir(os.getcwd()) if '.git' not in file]
    repo.index.add(files)
    message = 'Static site pushed with build timestamp %s' % build_timestamp
    repo.index.commit(message)
    repo.remotes.origin.push()


def clear_up(build_dir):
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)


def _filter_if_no_ready_measures(subtopics, beta_publication_states):
    filtered = []
    for st in subtopics:
        for m in st.children:
            if m.eligible_for_build(beta_publication_states):
                if st not in filtered:
                    filtered.append(st)
    return filtered


def _order_subtopics(topic, subtopics):
    ordered = []
    for st in topic.subtopics:
        for s in subtopics:
            if st == s.guid:
                ordered.append(s)
    return ordered


def _prettify(out):
    soup = BeautifulSoup(out, 'html.parser')
    return soup.prettify()
