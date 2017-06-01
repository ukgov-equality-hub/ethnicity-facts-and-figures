import os
import json

from collections import OrderedDict
from werkzeug.utils import secure_filename
import logging
import git

from application.cms.models import (
    Page,
    Meta,
    publish_status
)

from application.cms.exceptions import GitRepoNotFound, InvalidPageType, PageNotFoundException

logger = logging.getLogger(__name__)


def process_path(dictionary, path):
    split_path = path.split('/')
    if not split_path[0] in dictionary.keys():
        dictionary[split_path[0]] = OrderedDict()
    sub_path = '/'.join(split_path[1:])
    if sub_path:
        process_path(dictionary[split_path[0]], sub_path)


class GitStore:

    def __init__(self, config):
        self.base_directory = config['BASE_DIRECTORY']
        self.repo_dir = config['REPO_DIR']
        self.content_dir = config['CONTENT_DIR']
        self.remote_repo = config['GITHUB_REMOTE_REPO']
        self.push_enabled = config['PUSH_ENABLED']
        self.work_with_remote = config['WORK_WITH_REMOTE']
        self.repo = git.Repo(self.repo_dir)

        # If working with remote enabled we'll checkout
        # from remote branch
        if self.work_with_remote:
            origin = self.repo.remotes.origin
            origin.fetch()
            branch = config['REPO_BRANCH']
            self.repo.remotes.origin.fetch()
            if str(self.repo.active_branch) != branch:
                self.repo.git.checkout('remotes/origin/{}'.format(branch), b=branch)
            logger.info('GitStore initialised using branch %s', branch)

    def initialise_empty_store(self):
        content_dir = '%s/%s' % (self.repo_dir, self.content_dir)
        os.mkdir(content_dir)
        self.repo.index.add([content_dir])
        self.repo.index.commit('initial commit')

    def get_page_directory(self, guid):
        base_directory = '%s/%s' % (self.repo_dir, self.content_dir)
        for root, dirs, files in os.walk(base_directory):
            if "meta.json" in files:
                meta_file = "/".join((root, "meta.json"))
                with open(meta_file) as data_file:
                    data = json.load(data_file)
                    if data['guid'] == guid:
                        return root
        raise PageNotFoundException("No page found with GUID: %s" % guid)

    def put_page(self, page, message=None):
        try:
            page_dir = self.get_page_directory(page.guid)
        except PageNotFoundException:
            # Page does not exits, build path
            page_dir = '/'.join((self.get_page_directory(page.meta.parent), page.guid))
        if not os.path.isdir(page_dir):
            os.mkdir(page_dir)

        page_file = '%s/page.json' % page_dir
        meta_file = '%s/meta.json' % page_dir

        with open(page_file, 'w') as f:
            f.write(page.to_json())
        with open(meta_file, 'w') as f:
            f.write(page.meta.to_json())

        if message is None:
            message = "Initial commit for page: {}".format(page.title)
        self._update_repo(page_dir, message)

    def put_page_in_dir(self, page, content_sub_dir, message=None):

        page_dir = '%s/%s/%s' % (self.repo_dir, self.content_dir, content_sub_dir)
        if not os.path.isdir(page_dir):
            os.mkdir(page_dir)

        page_file = '%s/page.json' % page_dir
        meta_file = '%s/meta.json' % page_dir

        page_content = ''
        if page.meta.type == 'measure':
            page_content = page.to_json
        else:
            page_content = json.dumps({'title': page.title})

        with open(page_file, 'w') as f:
            f.write(page_content)
        with open(meta_file, 'w') as f:
            f.write(page.meta.to_json())

        if message is None:
            message = "Initial commit for page: {}".format(page.title)
        self._update_repo(page_dir, message)

    def put_meta(self, page, message):
        page_dir = self.get_page_directory(page.guid)
        meta_file = '%s/meta.json' % page_dir
        with open(meta_file, 'w') as f:
            f.write(page.meta.to_json())
        self._update_repo(page_dir, message)

    def put_dimension_json_data(self, page, dimension, data, file_name, message):
        page_dir = self.get_page_directory(page.guid)
        source_dir = '%s/source' % page_dir
        dimension_data_dir = '%s/%s' % (source_dir, dimension.guid)

        self.check_directory_exists(source_dir)
        self.check_directory_exists(dimension_data_dir)

        data_file = '%s/%s' % (dimension_data_dir, file_name)
        with open(data_file, 'w') as f:
            f.write(json.dumps(data))
        self._update_repo(page_dir, message)

    def get_dimension_json_data(self, page, dimension, file_name):
        page_dir = self.get_page_directory(page.guid)
        full_file_name = '%s/source/%s/%s' % (page_dir, dimension.guid, file_name)
        with open(full_file_name) as data_file:
            return json.load(data_file)

    def put_source_data(self, page, file):
        page_dir = self.get_page_directory(page.guid)
        filename = secure_filename(file.filename)
        source_dir = '%s/source' % page_dir
        self.check_dir(source_dir)

        full_file_name = '%s/%s' % (source_dir, filename)
        file.save(full_file_name)

    def check_dir(self, dir_name):
        if not os.path.isdir(dir_name):
            os.mkdir(dir_name)

    def list_source_data(self, guid, extension_list=['.csv', '.xls', '.xlsx', '.odf'], dimension=None):
        page_dir = self.get_page_directory(guid)
        source_dir = '%s/source' % page_dir
        if os.path.isdir(source_dir):
            return [f for f in os.listdir(source_dir)
                    if self.path_is_source_data('%s/%s' % (source_dir, f), extension_list)]
        else:
            return []

    def path_is_source_data(self, path, extension_list):
        filename, file_extension = os.path.splitext(path)
        return os.path.isfile(path) and file_extension in extension_list

    def check_directory_exists(self, directory):
        if not os.path.isdir(directory):
            os.mkdir(directory)

    # TODO lets change this to take a path and guid as caller knows path then
    # we don't need to search for page where meta.guid == guid or
    # at least we know the dir to search instead of walking directories from root
    def get(self, guid):
        page_dir = '%s/%s' % (self.repo_dir, self.content_dir)
        for root, dirs, files in os.walk(page_dir):
            if "meta.json" in files:
                meta_file = "/".join((root, "meta.json"))
                with open(meta_file) as data_file:
                    data = json.load(data_file)
                    if data['guid'] == guid:
                        page_file_path = '%s/page.json' % root
                        meta_file_path = '%s/meta.json' % root
                        page_json = self._file_content(page_file_path)
                        meta_json = self._file_content(meta_file_path)
                        meta = Meta(guid=meta_json.get('guid'),
                                    uri=meta_json.get('uri'),
                                    parent=meta_json.get('parent'),
                                    page_type=meta_json.get('type'),
                                    status=publish_status[meta_json.get('status').upper()])
                        if page_json.get('title') is not None:
                            return Page(title=page_json.get('title'),
                                        data=page_json,
                                        meta=meta,
                                        dimensions=page_json.get('dimensions'),
                                        uploads=self.list_source_data(meta_json.get('guid'))
                                        )
                        else:
                            return None
        raise PageNotFoundException()

    def get_pages(self):
        """"
            Will build a tree of pages. Tried to strike a balance between development time, efficiency and
            possible future requirements. Obviously maybe recursion, or object methods. One issue we face is the loose
            relationship between GUID, title and directory.
        """
        page_dir = '%s/%s' % (self.repo_dir, self.content_dir)
        page_tree = OrderedDict()

        for root, dirs, files in os.walk(page_dir):
            relative_path = root.replace(page_dir, '')
            if relative_path:
                process_path(page_tree, relative_path)

        object_tree = OrderedDict({})

        # Remove static pages, this is the simplest plan, on the basis that these pages may need to be editable
        # at some point.
        page_tree = page_tree['']
        static_pages = ["homepage"]
        for key in page_tree.keys():
            if key.startswith('static_'):
                static_pages.append(key)

        for static_page in static_pages:
            del page_tree[static_page]

        # Convert tree to objects
        for topic, subtopics in page_tree.items():
            try:
                if topic:
                    topic_obj = self.get(topic)
                    object_tree[topic_obj] = OrderedDict()
                    for subtopic, measures in subtopics.items():
                        subtopic_obj = self.get(subtopic)
                        if not subtopic_obj.meta:
                            raise AttributeError()
                        object_tree[topic_obj][subtopic_obj] = OrderedDict()
                        for measure, children in measures.items():
                            measure_obj = self.get(measure)
                            object_tree[topic_obj][subtopic_obj][measure_obj] = OrderedDict()
            except PageNotFoundException:
                pass

        return object_tree

    def get_pages_by_type(self, type):
        pages = []
        page_dir = '%s/%s' % (self.repo_dir, self.content_dir)
        for root, dirs, files in os.walk(page_dir):
            for dir in dirs:
                prefix = '%s_' % type
                if dir.startswith(prefix):
                    page = self.get(dir)
                    pages.append(page)
        return pages

    def _update_repo(self, page_dir, message):
        if not os.path.isdir(self.repo_dir):

            raise GitRepoNotFound('No repo found at: {}'.format(self.repo_dir))

        # TODO should this be re-enabled?
        # origin.pull(origin.refs[0].remote_head)

        self.repo.index.add([page_dir])
        self.repo.index.commit(message)

        # TODO let's do a pull rebase and push to origin
        if self.work_with_remote and self.push_enabled:
            origin = self.repo.remotes.origin
            origin.fetch()
            origin.push()

    def _file_content(self, page_file_path):
        with open(page_file_path) as data_file:
            data = json.loads(data_file.read())
        return data

    def get_subtopics(self, topic):
        path = '%s/%s/%s' % (self.repo_dir, self.content_dir, topic.meta.guid)
        files = os.listdir(path)
        subtopics = []
        for file in files:
            full_path = '%s/%s' % (path, file)
            if os.path.isdir(full_path):
                subtopics.append(file)
        return subtopics

    # TODO this may as well return the actual pages
    def get_measures(self, subtopic):
        path = '%s/%s/%s/%s' % (self.repo_dir, self.content_dir, subtopic.meta.parent, subtopic.meta.guid)
        files = os.listdir(path)
        measures = []
        for file in files:
            full_path = '%s/%s' % (path, file)
            if os.path.isdir(full_path):
                measures.append(file)
        return measures
