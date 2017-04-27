import os
import json
import git

from application.cms.exceptions import RepoAlreadyExists, GitRepoNotFound
from application.cms.models import (
    Page,
    Meta,
    publish_status
)


class GitStore:

    def __init__(self, config):
        self.base_directory = config['BASE_DIRECTORY']
        self.repo_dir = config['REPO_DIR']
        self.content_dir = config['CONTENT_DIR']
        self.remote_repo = config['GITHUB_REMOTE_REPO']
        self._get_or_create_content_repo()  # checks and initialises
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

        if not os.path.isdir(self.repo_dir):
            raise GitRepoNotFound('No repo found at: {}'.format(self.repo_dir))

        repo = self._get_or_create_content_repo()
        origin = repo.remotes.origin

        origin.fetch()
        # origin.pull(origin.refs[0].remote_head)
        repo.index.add([page_dir])
        repo.index.commit(message)

        # TODO maybe have this toggled by config?
        if self.push_enabled:
            origin.push()

    def _file_content(self, page_file_path):
        with open(page_file_path) as data_file:
            data = json.loads(data_file.read())
        return data

    def _get_or_create_content_repo(self):
        repo = self._get_content_repo()
        if repo is None:
            repo = self._create_content_repo()
        return repo

    def _get_content_repo(self):
        try:
            return git.Repo(self.repo_dir)
        except git.NoSuchPathError as e:
            print(e)
            return None

    def _create_content_repo(self):
        if not os.path.isdir(self.repo_dir):
            os.mkdir(self.repo_dir)
        repo = git.Repo.init(self.repo_dir)
        origin = repo.create_remote('origin', self.remote_repo)
        origin.fetch()
        origin.pull(origin.refs[0].remote_head)
        return repo
