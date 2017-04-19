import json
import os
import shutil

from git import Repo
from slugify import slugify

from application.cms.exceptions import PageExistsException

# TODO: This should be in config, this is specifically here to avoid a merge conflict because I know Adam has created a config
from manage import app

project_name = "rd_cms"
base_directory = app.config['BASE_DIRECTORY']
# Should point to content repo
content_repo = app.config['CONTENT_REPO']
content_directory = app.config['CONTENT_DIRECTORY']
git_content_repo = Repo(content_repo)

# The below is a bit odd, but WTForms will only populate a form with an object(not an object), this is transitional
# Option 1: Give the page all the attributes of the page.json dict, and meta.json (it would be useful to have meta)
# Option 2: Use library to convert dictionary to object in the view


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

# TODO split: TopicPage and MeasurementPage and inherit from below


class Page(object):
    def __init__(self, guid):
        self.guid = guid
        self.page_directory = '/'.join((content_directory, self.guid))

    def create_new_page(self, initial_data=None):
        """
        Has five main functions:
        1. Create the file/dir structure based on cms/page_template
        2. Update the meta.json with anything relevant
        3. Save the initial page.json content
        4. Add the files to the git repo and
        5. TODO: Push repo
        6. You could make this transactional, there are a lof of steps
        :param initial_data: dictionary representation of data to be placed in page.json
        :return:
        """
        # Create files
        self.create_page_files()
        # Update meta.json
        #TODO: Update this when we get more fields, currently it is basically a POC for updating meta.json
        updated_meta = {'uri': slugify(self.guid)}
        self.update_meta(updated_meta)

        # Save files contents, it's important at this point for commit history
        if initial_data:
            self.save_content(initial_data)

        # Add to git
        git_content_repo.index.add([self.page_directory])
        #git_content_repo.index.commit("Initial commit for page: {}".format(self.guid))

        # Push repo

    def create_page_files(self):
        """Copies the contents of page_template to the /pages/folder/destination"""
        source = '/'.join((base_directory, 'page_template/'))
        destination = '/'.join((content_directory, self.guid))

        if os.path.exists(destination):
            raise PageExistsException('This page already exists')
        else:
            # Page can be created
            shutil.copytree(source, destination)

            # TODO: This stuff will apply to measurement pages
            # src_directory = "/".join((destination, "source"))
            # data_directory = "/".join((destination, "data"))
            # # Check directories have been created
            # # if type == "measurement":
            # #     if not os.path.exists(src_directory):
            # #         os.makedirs(src_directory)
            # #     if not os.path.exists(data_directory):
            # #         os.makedirs(data_directory)

    def save_content(self, data):
        """
        Updates the relevant page.json.
        :param data: (dictionary) dictionary of all the data that will be stored in page.json (we may later want this
         to do a patch/delta on that data, it would be safer)
        :return: None
        """
        with open('/'.join((self.page_directory, 'page.json')), 'w') as page_json:
            json.dump(data, page_json)

    def page_content(self):
        """
        Updates the relevant page.json.
        :param name: (str) name of the page being loaded
        :return: a object containing the contents of page.json
        """
        with open('/'.join((self.page_directory, 'page.json'))) as data_file:
            data = json.loads(data_file)
        return data

    def update_meta(self, new_data):
        """
        Meta is going to do what content does not, it is going to act like a patch request, the meta and content methods
        can be merged into one, at some point.
        :return:
        """
        meta_file = '/'.join((self.page_directory, 'meta.json'))
        with open(meta_file) as meta_content:
            file_data = json.loads(meta_content.read())
        for key, value in new_data.items():
            file_data[key] = value
        with open(meta_file, 'w') as meta_content:
            json.dump(file_data, meta_content)

    def publish_status(self):
        pass

    def publish(self):
        pass

    def parent(self):
        pass

    def children(self):
        pass

