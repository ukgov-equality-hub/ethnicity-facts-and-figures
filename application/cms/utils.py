import os
import warnings

import git
from git import Repo
from application.cms.exceptions import InvalidBranchSpecified, RepoAlreadyExists

# Very much a work in progress

valid_branches = ['draft', 'department-review', 'internal-review', 'approved']


class Storage(object):
    def __init__(self, config):
        self.repo_name_prefix = config['CONTENT_REPO']
        self.content_repos = config['REPOS_DIRECTORY']
        self.remote_repo = "https://{}:x-oauth-basic@{}.git".format(config['GITHUB_ACCESS_TOKEN'],
                                                                    '/'.join((config['GITHUB_URL'],
                                                                              config['CONTENT_REPO'])))

    def check_branch_name_valid(self, branch_name):
        if branch_name not in valid_branches:
            raise InvalidBranchSpecified("Branch {} must be one of draft, "
                                         "internal-review, department-review and approved"
                                         .format(branch_name))

    def check_content_repo_exists(self, branch):
        self.check_branch_name_valid(branch)
        repo_name = '_'.join((self.repo_name_prefix, branch))
        repo_dir = "/".join((self.content_repos, repo_name))
        if not os.path.isdir(repo_dir):
            return False
        else:
            # Path exists, check branch TODO: split out branch check
            repo = Repo(repo_dir)
            current_branch_name = str(repo.active_branch)
            if branch != current_branch_name:
                warnings.warn("Branch {} does not match requested branch {}".format(current_branch_name, branch))
            return True

    def create_content_repo(self, branch):
        # TODO: ensure not bare_repo
        self.check_branch_name_valid(branch)
        repo_name = '_'.join((self.repo_name_prefix, branch))
        repo_dir = "/".join((self.content_repos, repo_name))
        if os.path.isdir(repo_dir):
            raise RepoAlreadyExists('Repo already exists at {}'.format(repo_dir))
        else:
            print(self.remote_repo)
            os.mkdir(repo_dir)
            repo = git.Repo.init(repo_dir)
            origin = repo.create_remote('origin', self.remote_repo)
            origin.fetch()
            origin.pull(origin.refs[0].remote_head)
            # Checkout remote branch
            repo.git.checkout('remotes/origin/{}'.format(branch), b=branch)

    def get_or_create_content_repo(self, branch):
        self.check_branch_name_valid(branch)
        if not self.check_content_repo_exists(branch):
            self.create_content_repo(branch)

    def create_all_content_repos(self):
        for branch in valid_branches:
            self.get_or_create_content_repo(branch)
