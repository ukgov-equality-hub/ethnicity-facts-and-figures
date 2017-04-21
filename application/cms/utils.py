import os
import warnings

import git
import subprocess
from git import Repo
from application.cms.exceptions import InvalidBranchSpecified, RepoAlreadyExists
from manage import app

# TODO: This will probably form another class

valid_branches = ['draft', 'department-review', 'internal-review', 'approved']
repo_name_prefix = app.config['CONTENT_REPO']
content_repos = app.config['REPOS_DIRECTORY']
remote_repo = "https://{}:x-oauth-basic@{}.git".format(app.config['GITHUB_ACCESS_TOKEN'],
                                                       '/'.join((app.config['GITHUB_URL'],
                                                                 app.config['CONTENT_REPO'])))


def check_branch_name_valid(branch_name):
    if branch_name not in valid_branches:
        raise InvalidBranchSpecified("Branch {} must be one of draft, internal-review, department-review and approved"
                                     .format(branch_name))


def check_content_repo_exists(branch):
    check_branch_name_valid(branch)
    repo_name = '_'.join((repo_name_prefix, branch))
    repo_dir = "/".join((content_repos, repo_name))
    if not os.path.isdir(repo_dir):
        return False
    else:
        # Path exists, check branch TODO: split out branch check
        repo = Repo(repo_dir)
        current_branch_name = str(repo.active_branch)
        if branch != current_branch_name:
            warnings.warn("Branch {} does not match requested branch {}".format(current_branch_name, branch))
        return True


def create_content_repo(branch):
    # TODO: ensure not bare_repo
    check_branch_name_valid(branch)
    repo_name = '_'.join((repo_name_prefix, branch))
    repo_dir = "/".join((content_repos, repo_name))
    if os.path.isdir(repo_dir):
        raise RepoAlreadyExists('Repo already exists at {}'.format(repo_dir))
    else:
        print(remote_repo)
        os.mkdir(repo_dir)
        repo = git.Repo.init(repo_dir)
        origin = repo.create_remote('origin', remote_repo)
        origin.fetch()
        origin.pull(origin.refs[0].remote_head)
        # Checkout remote branch
        repo.git.checkout('remotes/origin/{}'.format(branch), b=branch)


def get_or_create_content_repo(branch):
    check_branch_name_valid(branch)
    if not check_content_repo_exists(branch):
        create_content_repo(branch)


def create_all_content_repos():
    for branch in valid_branches:
        get_or_create_content_repo(branch)
