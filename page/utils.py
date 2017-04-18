import json
import shutil
import os


from page.exceptions import PageExistsException

# TODO: These utils can form the basis for a page class later, all these methods should be considered in-flux

# TODO: This should be in config, this is specifically here to avoid a merge conflict because I know Adam has created a config
project_name = "rd_cms"
base_directory = "/".join((os.path.dirname(os.path.dirname(os.path.abspath(__file__))), project_name))

def create_page(name, type):
    """
    Copies the empty page structure from page_template to the destination, adds it content git repo
    ARGS:
        :param name (str): The name of the page, a folder will be created with this name in the content repo
        :param type (str): [topic, measurement] Measurement pages have src and data directories, this is a temporary arg,
                    in the future this will be handled as part of the page class
    """
    # TODO: Update the destination var to point to content repo, add and commit to repo
    # Potentially later creating and adding/commit should be split
    # Also consider splitting create topic page
    # Create the page
    source = '/'.join((base_directory, 'page_template/'))
    destination = '/'.join((base_directory, 'pages', name))
    print(destination)

    if os.path.exists(destination):
        raise PageExistsException('This page already exists')
    else:
        # Page can be created
        shutil.copytree(source, destination)
        src_directory = "/".join((destination, "source"))
        data_directory = "/".join((destination, "data"))
        # Check directories have been created
        if type == "measurement":
            if not os.path.exists(src_directory):
                os.makedirs(src_directory)
            if not os.path.exists(data_directory):
                os.makedirs(data_directory)


def save_page(name, data):
    """
    Updates the relevant page.json.
    :param name: (str) name of the page being updated
    :param data: (dictionary) dictionary of all the data that will be stored in page.json (we may later want this
     to do a patch/delta on that data, it would be safer)
    :return: None
    """
    page_directory = '/'.join((base_directory, 'pages', name))
    with open('/'.join((page_directory, 'page.json')), 'w') as page_json:
        json.dump(data, page_json)


def publish():
    pass

