import os
import json
import shutil

from datetime import date
from functools import wraps

from flask import render_template
from flask_security import current_user

from git import Repo
from application.cms.exceptions import RepoAlreadyExists, GitRepoNotFound, BranchNotFound


def create_content_repo(destination):
    if os.path.isdir(destination):
        repo = Repo(destination)
    else:
        os.mkdir(destination)
        repo = Repo.init(destination)
    return repo


def check_branch_checked_out(repo_directory, branch):
    repo = Repo(repo_directory)
    current_branch_name = str(repo.active_branch)
    if branch == current_branch_name:
        return True
    else:
        return False


def check_out_branch(repo_directory, branch):
    repo = Repo(repo_directory)
    current_branch_name = str(repo.active_branch)
    origin = repo.remotes.origin
    origin.fetch()

    if branch != current_branch_name:

        for local_branch in repo.branches:
            if branch == str(local_branch):
                local_branch.checkout()
                return

        for remote_branch in origin.refs:
            if "origin/{}".format(branch) == str(remote_branch):
                repo.git.checkout('remotes/origin/{}'.format(branch), b=branch)
                return

        raise BranchNotFound('Branch {} does not exist locally or in remote'.format(branch))


def get_or_create_content_repo(remote_repo, destination, work_with_remote):
    repo = create_content_repo(destination)
    if work_with_remote:
        exists = [x for x in repo.remotes if x.name == 'origin']
        if not exists:
            origin = repo.create_remote('origin', remote_repo)
            origin.fetch()


def clear_content_repo(repo_dir):
    if os.path.isdir(repo_dir):
        shutil.rmtree(repo_dir)


def internal_user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous or current_user.is_internal_user():
            return f(*args, **kwargs)
        else:
            return render_template('static_site/not_allowed.html')
    return decorated_function


class DateEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, date):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)