import os
import json

from collections import OrderedDict
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
        dictionary[split_path[0]]=OrderedDict()
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

        self.repo = git.Repo(self.repo_dir)
        origin = self.repo.remotes.origin
        origin.fetch()
        branch = config['REPO_BRANCH']
        if str(self.repo.active_branch) != branch:
            self.repo.git.checkout('remotes/origin/{}'.format(branch), b=branch)
        logger.info('GitStore initialised using branch %s', branch)

    def put_page(self, page, message=None):

        page_dir = '%s/%s/%s' % (self.repo_dir, self.content_dir, page.guid)
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
        # self._update_repo(page_dir, message)

    def put_meta(self, page, message):
        page_dir = '%s/%s/%s' % (self.repo_dir, self.content_dir, page.guid)
        meta_file = '%s/meta.json' % page_dir
        with open(meta_file, 'w') as f:
            f.write(page.meta.to_json())
        self._update_repo(page_dir, message)

    def get(self, guid):
        print("GUID:", guid)
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
                            return Page(title=page_json.get('title'), description=page_json.get('description'),
                                        meta=meta)
                        else:
                            return None
        raise PageNotFoundException()

    def list(self):
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
                        print("Subtopic: ", subtopic)
                        if not subtopic_obj.meta:
                            raise AttributeError()
                        object_tree[topic_obj][subtopic_obj] = OrderedDict()
                        for measure, children in measures.items():
                            measure_obj = self.get(measure)
                            object_tree[topic_obj][subtopic_obj][measure_obj] = OrderedDict()
            except PageNotFoundException:
                pass

        print(object_tree)
        return object_tree

    def _update_repo(self, page_dir, message):
        if not os.path.isdir(self.repo_dir):

            raise GitRepoNotFound('No repo found at: {}'.format(self.repo_dir))

        origin = self.repo.remotes.origin

        origin.fetch()

        # TODO should this be re-enabled?
        # origin.pull(origin.refs[0].remote_head)

        self.repo.index.add([page_dir])
        self.repo.index.commit(message)

        if self.push_enabled:
            origin.push()

    def _file_content(self, page_file_path):
        with open(page_file_path) as data_file:
            data = json.loads(data_file.read())
        return data
