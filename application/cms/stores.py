import os
import json
import git

from application.cms.models import (
    Page,
    Meta,
    publish_status
)

from application.cms.exceptions import GitRepoNotFound


class GitStore:

    def __init__(self, config):
        self.base_directory = config['BASE_DIRECTORY']
        self.repo_dir = config['REPO_DIR']
        self.content_dir = config['CONTENT_DIR']
        self.remote_repo = config['GITHUB_REMOTE_REPO']
        self.repo = git.Repo(self.repo_dir)
        self.push_enabled = config['PUSH_ENABLED']

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
        self._update_repo(page_dir, message)

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
        meta = Meta(uri=meta_json.get('uri'),
                    parent=meta_json.get('parent'),
                    page_type=meta_json.get('type'),
                    status=publish_status[meta_json.get('status').upper()])
        if page_json.get('title')is not None:
            return Page(title=page_json.get('title'), description=page_json.get('description'), meta=meta)

    def list(self):
        page_dir = '%s/%s' % (self.repo_dir, self.content_dir)
        pages = [page for page in os.listdir(page_dir) if page.startswith('topic')]
        page_list = []
        for page in pages:
            page_obj = self.get(page)
            page_list.append(page_obj)
        return page_list

    def _update_repo(self, page_dir, message):
        git_file = '%s/.git'
        if not os.path.isfile(git_file):
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
