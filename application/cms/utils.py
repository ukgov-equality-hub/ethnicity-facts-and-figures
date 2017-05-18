import os
import shutil
import git

from git import Repo
from application.cms.exceptions import RepoAlreadyExists, GitRepoNotFound, BranchNotFound


def check_content_repo_exists(destination):
    if not os.path.isdir(destination):
        return False
    else:
        # Path exists, check it's a git repo
        repo = Repo(destination)
        return True


def create_content_repo(remote_repo, destination):
    if os.path.isdir(destination):
        raise RepoAlreadyExists('Repo already exists at {}'.format(destination))
    else:
        os.mkdir(destination)
        repo = git.Repo.init(destination)
        origin = repo.create_remote('origin', remote_repo)
        origin.fetch()


def check_branch_checked_out(repo_directory, branch):
    if not check_content_repo_exists(repo_directory):
        raise GitRepoNotFound('No repo at {}'.format(repo_directory))

    repo = Repo(repo_directory)
    current_branch_name = str(repo.active_branch)
    if branch == current_branch_name:
        return True
    else:
        return False


def check_out_branch(repo_directory, branch):
    if not check_content_repo_exists(repo_directory):
        raise GitRepoNotFound('No repo at {}'.format(repo_directory))
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


def get_or_create_content_repo(remote_repo, destination):
    if not check_content_repo_exists(destination):
        create_content_repo(remote_repo, destination)


def clear_content_repo(repo_dir):
    if os.path.isdir(repo_dir):
        shutil.rmtree(repo_dir)
