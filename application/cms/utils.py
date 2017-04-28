import os
import shutil
import warnings

import git
from git import Repo
from application.cms.exceptions import RepoAlreadyExists


def check_content_repo_exists(destination, branch=None):
    if not os.path.isdir(destination):
        return False
    else:
        # Path exists, check branch TODO: split out branch check
        repo = Repo(destination)
        current_branch_name = str(repo.active_branch)
        if branch and branch != current_branch_name:
            warnings.warn("Branch {} does not match requested branch {}".format(current_branch_name, branch))
        return True


def create_content_repo(remote_repo, destination, branch=None):
    git_file = '%s/.git'
    if os.path.isfile(git_file):
        raise RepoAlreadyExists('Repo already exists at {}'.format(destination))
    else:
        os.mkdir(destination)
        repo = git.Repo.init(destination)
        origin = repo.create_remote('origin', remote_repo)
        origin.fetch()
        origin.pull(origin.refs[0].remote_head)


def get_or_create_content_repo(remote_repo, destination, branch=None):
    if not check_content_repo_exists(destination, branch):
        create_content_repo(remote_repo, destination)


def clear_content_repo(repo_dir):
    if os.path.isdir(repo_dir):
        shutil.rmtree(repo_dir)
