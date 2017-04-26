import json
import os
import shutil

from bidict import bidict
from git import Repo
from slugify import slugify
from application.cms.exceptions import (
    PageExistsException,
    RejectionImpossible,
    AlreadyApproved,
    FileUnEditable,
    GitRepoNotFound,
    CommitMessageCannotBeEmpty, PageUnEditable, CannotPublishRejected)
from application.cms.utils import check_content_repo_exists

publish_status = bidict(
    REJECTED=0,
    DRAFT=1,
    INTERNAL_REVIEW=2,
    DEPARTMENT_REVIEW=3,
    ACCEPTED=4
)

# The below is a bit odd, but WTForms will only populate a form with an
# object(not an object), this is transitional
# Option 1: Give the page all the attributes of the page.json dict,
# and meta.json (it would be useful to have meta)
# Option 2: Use library to convert dictionary to object in the view


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

# TODO split: TopicPage and MeasurementPage and inherit from below
# TODO: YOU CANNOT EDIT REJECTED PAGES AT PRESENT


class Page(object):
    def __init__(self, guid, config):
        self.guid = guid
        self.base_directory = config['BASE_DIRECTORY']
        self.repo_dir = config['REPO_DIR']
        self.content_dir = config['CONTENT_DIR']
        self.page_dir = '/'.join((self.repo_dir, self.content_dir, self.guid))
        self.repo = Repo(self.repo_dir)

    def create_new_page(self, initial_data=None):
        """
        Has five main functions:
        1. Create the file/dir structure based on cms/page_template
        2. Update the meta.json with anything relevant
        3. Save the initial page.json content
        4. Add the files to the git repo and
        5. TODO: Push repo
        6. You could make this transactional, there are a lof of steps
        :param initial_data: dictionary representation of data to be
        placed in page.json
        :return:
        """
        # Create files
        self.create_page_files()
        # Update meta.json
        updated_meta = {'uri': slugify(self.guid)}
        self.update_meta_data(updated_meta)

        # Save files contents, it's important at this point for commit history
        if initial_data:
            self.update_page_data(initial_data)

        msg = "Initial commit for page: {}".format(self.guid)
        self.update_git_repo(msg)

    def create_page_files(self):
        """Copies the contents of page_template to the
        /pages/folder/destination"""
        source = '/'.join((self.base_directory, 'page_template/'))

        if os.path.exists(self.page_dir):
            raise PageExistsException('This page already exists')
        else:
            # Page can be created
            shutil.copytree(source, self.page_dir)

            # TODO: This stuff will apply to measurement pages
            # src_directory = "/".join((destination, "source"))
            # data_directory = "/".join((destination, "data"))
            # # Check directories have been created
            # # if type == "measurement":
            # #     if not os.path.exists(src_directory):
            # #         os.makedirs(src_directory)
            # #     if not os.path.exists(data_directory):
            # #         os.makedirs(data_directory)

    def update_page_data(self, new_data, commit_message=None):
        """This is a wrapper around update file contents, it will exclusively update page.json
        It will also send any rejected state pages to internal review, and check that the page is in an editable state.
        :param new_data
        :param commit_message
        :return None
        """
        # if status is not draft or rejected, this page cannot be edited
        num_status = publish_status[self.publish_status()]
        if num_status >= 2:
            raise PageUnEditable('Only pages in DRAFT or REJECT can be edited')
        else:
            # update page
            self.update_file_contents(new_data, 'page.json', commit_message)
            # if currently rejected, update state to internal review
            print('NUM_STATUS', num_status)
            if num_status == 0:
                new_status = publish_status.inv[2]
                self.update_status(new_status)

    def update_meta_data(self, new_data, commit_message=None):
        """This is a wrapper around update file contents, it will exclusively update page.json
        :param new_data
        :param commit_message
        :return None
        """
        # TODO: This should be effectively private
        self.update_file_contents(new_data, 'meta.json', commit_message)

    def update_file_contents(self, new_data, file, commit_message=None):
        """
        Updates the relevant json file. DO NOT USE OUTSIDE CLASS. use update_page_data or update_meta_data
        :param file:  the file you wish to update, must be meta.json or page.json
        :param data: (dictionary) dictionary of all the data that
        will be stored in page.json (we may later want this
         to do a patch/delta on that data, it would be safer)
        :return: None
        """
        if file not in ['meta.json', 'page.json']:
            raise FileUnEditable("Only meta.json & page.json can be updated, not {}".format(file))
        full_path = '/'.join((self.page_dir, file))
        with open(full_path) as file_content:
            file_data = json.loads(file_content.read())
        for key, value in new_data.items():
            file_data[key] = value
        with open(full_path, 'w') as file_content:
            json.dump(file_data, file_content)

        if not commit_message:
            commit_message = "Contents updated in file: {}/{}".format(self.guid, file)
        self.update_git_repo(commit_message)

    def file_content(self, file):
        """
        Retrieves contents of page.json
        :param name: (str) name of the page being loaded
        :return: a dictionary containing the contents of page.json
        """
        with open('/'.join((self.page_dir, file))) as data_file:
            data = json.loads(data_file.read())
        return data

    def publish_status(self, numerical=False):
        current_status = self.file_content('meta.json')['status'].upper()
        if numerical:
            return publish_status[current_status]
        else:
            return current_status

    def available_actions(self):
        """Returns the states available for this page -- WIP"""
        # TODO: SINCE REJECT AND PUBLISH(APPROVE) are methods, EDIT should be a method as well
        # The above todo can come as part of the storage/page refactor
        num_status = self.publish_status(numerical=True)
        states = []
        if num_status == 4:  # if it's ACCEPTED you can't do anything
            return states
        if num_status <= 1:  # if it's rejected or draft you can edit it
            states.append('UPDATE')
        if num_status >= 1:  # if it isn't REJECTED or ACCEPTED you can APPROVE it
            states.append('APPROVE')
        if num_status in [2, 3]:  # if it is in INTERNAL or DEPARTMENT REVIEW it can be rejected
            states.append('REJECT')
        return states

    def publish(self):
        """Sends page to next state"""
        # TODO: this should be refactored to be called something else
        num_status = self.publish_status(numerical=True)
        if num_status == 0:
            # You can only get out of rejected state by saving
            message = "Page: {} is rejected.".format(self.guid)
            raise CannotPublishRejected(message)
        elif num_status <= 3:
            new_status = publish_status.inv[num_status+1]
            self.update_status(new_status)
        else:
            message = "Page: {} is already approved.".format(self.guid)
            raise AlreadyApproved(message)

    def update_status(self, status):
        """Sets a page to have a specific status in meta,
         should all be called from within this class"""
        # Update meta
        msg = "Updating page state for page: {} from {} to {}".format(self.guid, self.publish_status(), status)
        self.update_meta_data({'status': '{}'.format(status)}, commit_message=msg)

    def reject(self):
        current_status = (self.publish_status())
        num_status = self.publish_status(numerical=True)
        if num_status in [0, 1, 4]:
            # You can't reject a rejected page, a draft page or a approved page.
            message = "Page {} cannot be rejected a page in state: {}.".format(self.guid, current_status)  # noqa
            raise RejectionImpossible(message)
        rejected_state = publish_status.inv[0]
        msg = "Updating page state for page: {} from {} to {}".format(self.guid, current_status, rejected_state)
        self.update_meta_data({'status': '{}'.format(rejected_state)}, commit_message=msg)

    def update_git_repo(self, commit_message):
        # Check the repo still exits
        if not check_content_repo_exists(self.repo_dir):
            raise GitRepoNotFound('No repo found at: {}'.format(self.repo_dir))
        # Pull the repo
        origin = self.repo.remotes.origin
        origin.fetch()
        origin.pull(origin.refs[0].remote_head)
        # Add files
        self.repo.index.add([self.page_dir])
        # Commit
        if not commit_message:
            raise CommitMessageCannotBeEmpty('Cannot create a commit without a commit message')

        self.repo.index.commit(commit_message)
        # Push
        origin.push()
