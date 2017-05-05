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

from application.cms.exceptions import GitRepoNotFound, InvalidPageType


logger = logging.getLogger(__name__)


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
        page_dir = '%s/%s' % (self.repo_dir, self.content_dir)
        page_file_path = '%s/%s/page.json' % (page_dir, guid)
        meta_file_path = '%s/%s/meta.json' % (page_dir, guid)
        page_json = self._file_content(page_file_path)
        meta_json = self._file_content(meta_file_path)
        meta = Meta(guid=meta_json.get('guid'),
                    uri=meta_json.get('uri'),
                    parent=meta_json.get('parent'),
                    page_type=meta_json.get('type'),
                    status=publish_status[meta_json.get('status').upper()])
        if page_json.get('title')is not None:
            return Page(title=page_json.get('title'), description=page_json.get('description'), meta=meta)
        else:
            return None

    def list(self):
        """"
            Will build a tree of pages. Tried to strike a balance between development time, efficiency and
            possible future requirements. Obviously maybe recursion, or object methods. One issue we face is the loose
            relationship between GUID, title and directory.
        """
        page_dir = '%s/%s' % (self.repo_dir, self.content_dir)
        pages = [page for page in os.listdir(page_dir)]

        page_tree_guids = OrderedDict({})

        for page in pages:
            if page.startswith('topic_'):
                page_obj = self.get(page)
                page_tree_guids[page_obj.guid] = OrderedDict()

        for i, page in enumerate(pages):
            if page.startswith('subtopic_'):
                page_obj = self.get(page)
                try:
                    parent = self.get(page_obj.meta.parent)
                    page_tree_guids[parent.guid][page_obj.guid] = OrderedDict()
                    del pages[i]
                except FileNotFoundError:
                    # Parent topic does not exist
                    pass

        for i, page in enumerate(pages):
            if page.startswith('measure_'):
                page_obj = self.get(page)
                parent_subtopic = page_obj.meta.parent
                for topic, children in page_tree_guids.items():
                    for subtopic, child in children.items():
                        if subtopic == parent_subtopic:
                            page_tree_guids[topic][parent_subtopic][page_obj.guid] = OrderedDict()

        object_tree = OrderedDict({})

        # Convert tree to objects, this could be recursive
        for topic, subtopics in page_tree_guids.items():
            topic_obj = self.get(topic)
            object_tree[topic_obj] = OrderedDict()
            for subtopic, measures in subtopics.items():
                subtopic_obj = self.get(subtopic)
                object_tree[topic_obj][subtopic_obj] = OrderedDict()
                for measure, children in measures.items():
                    measure_obj = self.get(measure)
                    object_tree[topic_obj][subtopic_obj][measure_obj] = OrderedDict()

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
