#! /usr/bin/env python
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from git import Repo

from flask import current_app, render_template
from application.factory import create_app
from application.config import Config, DevConfig

executor = ThreadPoolExecutor(max_workers=1)


# TODO see if it might be just as easy to use app test client to do GET requests
# then again that means keep a logged in user


def do_it(application):
    with application.app_context():
        base_build_dir = application.config['BUILD_DIR']
        if not os.path.isdir(base_build_dir):
            os.mkdir(base_build_dir)
        build_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S.%f')

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
            topic_dir = '%s/%s' % (build_dir, topic.meta.uri)
            if not os.path.exists(topic_dir):
                os.mkdir(topic_dir)
            subtopics = page_service.get_subtopics(topic)
            build_subtopic_pages(subtopics, topic, topic_dir)
            build_measure_pages(page_service, subtopics, topic, topic_dir)

        push_site(build_dir, build_timestamp)
        # clear_up(build_dir)


def build_subtopic_pages(subtopics, topic, topic_dir):
    out = render_template('static_site/topic.html',
                          page=topic,
                          subtopics=subtopics,
                          asset_path='/static/',
                          static_mode=True)
    file_path = '%s/index.html' % topic_dir
    with open(file_path, 'w') as out_file:
        out_file.write(out)


def build_measure_pages(page_service, subtopics, topic, topic_dir):
    for st in subtopics:
        for mp in st['measures']:
            measure_page = page_service.get_page(mp.meta.guid)
            # TODO needs a publication date <= now
            if measure_page.meta.status in ['ACCEPTED']:
                measure_dir = '%s/%s/measure' % (topic_dir, st['subtopic'].meta.uri)
                if not os.path.exists(measure_dir):
                    os.makedirs(measure_dir)
                measure_file = '%s/%s.html' % (measure_dir, mp.meta.uri)
                dimensions = [d.__dict__() for d in measure_page.dimensions]
                out = render_template('static_site/measure.html',
                                      topic=topic.meta.uri,
                                      measure_page=measure_page,
                                      dimensions=dimensions,
                                      asset_path='/static/',
                                      static_mode=True)

                with open(measure_file, 'w') as out_file:
                    out_file.write(out)


def build_homepage(topics, site_dir, build_timestamp=None):
    out = render_template('static_site/index.html',
                          topics=topics,
                          asset_path='/static/',
                          build_timestamp=build_timestamp,
                          static_mode=True)
    file_path = '%s/index.html' % site_dir
    with open(file_path, 'w') as out_file:
        out_file.write(out)


def pull_current_site(build_dir, remote_repo):
    repo = Repo.init(build_dir)
    origin = repo.create_remote('origin', remote_repo)
    origin.fetch()
    repo.create_head('master', origin.refs.master).set_tracking_branch(origin.refs.master).checkout()
    origin.pull()


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
