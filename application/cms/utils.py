import os
import warnings

import git
from git import Repo
from application.cms.exceptions import RepoAlreadyExists


def check_content_repo_exists(destination, branch=None):
    if not os.path.isdir(destination):
        return False
    else:
        # Path exists, check branch TODO: split out branch check
        if branch:
            repo = Repo(destination)
            current_branch_name = str(repo.active_branch)
            if branch and branch != current_branch_name:
                warnings.warn("Branch {} does not match requested branch {}".format(current_branch_name, branch))
        return True


def create_content_repo(remote_repo, destination, branch=None):
    if os.path.isdir(destination):
        raise RepoAlreadyExists('Repo already exists at {}'.format(destination))
    else:
        os.mkdir(destination)
        repo = git.Repo.init(destination)
        origin = repo.create_remote('origin', remote_repo)
        origin.fetch()
        origin.pull(origin.refs[0].remote_head)
        # # Checkout remote branch
        # if branch:
        #     repo.git.checkout('remotes/origin/{}'.format(branch))


def get_or_create_content_repo(remote_repo, destination, branch=None):
    if not check_content_repo_exists(destination, branch):
        create_content_repo(remote_repo, destination, branch)
