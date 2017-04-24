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
    FileUnEditable)

publish_status = bidict(
    REJECTED=0,
    DRAFT=1,
    INTERNAL_REVIEW=2,
    DEPARTMENT_REVIEW=3,
    APPROVED=4
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
        self.update_file_contents(updated_meta, 'meta.json')

        # Save files contents, it's important at this point for commit history
        if initial_data:
            self.update_file_contents(initial_data, 'page.json')

        # Add to git,
        # TODO, This should use the same mechanism as publish
        try:
            self.repo.index.add([self.page_dir])
        except Exception as e:
            print("Do nothing for now heroku")
        # Push repo
        # self.repo.index.commit("Initial commit for page: {}".format(self.guid)) # noqa

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

    def update_file_contents(self, new_data, file):
        """
        Updates the relevant page.json.
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

    def file_content(self, file):
        """
        Retrieves contents of page.json
        :param name: (str) name of the page being loaded
        :return: a dictionary containing the contents of page.json
        """
        with open('/'.join((self.page_dir, file))) as data_file:
            data = json.loads(data_file.read())
        return data

    def publish_status(self):
        # TODO: provide numeric or string
        return self.file_content('meta.json')['status']

    def publish(self):
        """Sends page to next state"""
        current_status = (self.publish_status()).upper()
        num_status = publish_status[current_status]
        if num_status == 0:
            """You can only get out of rejected state by saving"""
            pass
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
        self.update_file_contents({'status': '{}'.format(status)}, 'meta.json')

    def reject(self):
        current_status = (self.publish_status()).upper()
        num_status = publish_status[current_status]
        if num_status in [0, 1, 4]:
            # You can't reject a rejected page,
            # a draft page or a approved page.
            message = "Page {} cannot be rejected a page in state: {}.".format(self.guid, current_status)  # noqa
            raise RejectionImpossible(message)
        self.update_file_contents({'status': '{}'.format(publish_status.inv[0])}, 'meta.json')
