import os
import csv
import yaml

from flask import (
    render_template,
    abort,
    redirect,
    url_for,
    request
)

from flask_security import login_required
from application.cms.utils import internal_user_required

from flask_security import (
    roles_required,
    current_user
)

from application.static_site import static_site_blueprint
from application.cms.page_service import page_service


@static_site_blueprint.route('/')
@internal_user_required
@login_required
def index():
    # temporarily load some data from yaml
    current_path = os.path.dirname(__file__)
    yaml_path = '%s/%s' % (current_path, 'data/copy/headline.yaml')
    with open(yaml_path, 'r') as yaml_file:
        data = yaml.load(yaml_file)

    return render_template('content.html', page=data)


@static_site_blueprint.route('/<topic>')
@internal_user_required
@login_required
def topic(topic):
    # temporarily load some data from yaml and csv
    current_path = os.path.dirname(__file__)
    yaml_path = '%s/%s' % (current_path, 'data/copy/topic_descriptions.yaml')
    with open(yaml_path, 'r') as yaml_file:
        data = yaml.load(yaml_file)
    topic_data = [t for t in data if t['name'] == topic]
    if topic_data:
        topic_data = topic_data[0]

    csv_path = '%s/%s' % (current_path, 'data/taxonomy.csv')
    all_data = []
    with open(csv_path, 'r') as file_data:
        reader = csv.DictReader(file_data, ('name', 'parent name', 'uri', 'parent uri', 'description'))
        for row in reader:
            all_data.append(row)

    parent_uri = '/%s' % topic
    data = [item for item in all_data if item['parent uri'] == parent_uri]
    for item in data:
        subtopic_name = '%s_t3' % item['name']
        subtopics = [t for t in all_data if t['parent name'] == subtopic_name]
        item['t3'] = subtopics

    return render_template('topic.html', page=topic_data, data=data)


@static_site_blueprint.route('/<topic>/<subtopic>/measure/<measure>')
@login_required
def measure_page(topic, subtopic, measure):

    # if request is for unemployment page for testing fetch data from yaml, csv etc.
    if measure == 'unemployment-in-the-uk':
        current_path = os.path.dirname(__file__)
        yaml_path = '%s/%s' % (current_path, 'data/copy/unemploymentintheuk.yaml')
        with open(yaml_path, 'r') as yaml_file:
            page_data = yaml.load(yaml_file)

        csv_path = '%s/%s' % (current_path, 'data/taxonomy.csv')
        all_data = []
        with open(csv_path, 'r') as file_data:
            reader = csv.DictReader(file_data, ('name', 'parent name', 'uri', 'parent uri', 'description'))
            for row in reader:
                all_data.append(row)

        parent_data = [item for item in all_data if item['uri'] == '/%s' % topic][0]
        article_data = [item for item in all_data if item['uri'] == '/%s' % measure]  # ?

        return render_template('article_1.html', data=article_data, parent=parent_data, page=page_data)

    else:
        # This is how it should really work

        subtopic_guid = 'subtopic_%s' % subtopic
        measure_guid = page_service.get_measure_guid(subtopic_guid, measure)
        if measure_guid is None:
            abort(404)
        measure_page = page_service.get_page(measure_guid)

        if current_user.is_departmental_user():
            if measure_page.meta.status not in ['DEPARTMENT_REVIEW', 'ACCEPTED']:
                return render_template('not_ready_for_review.html')
        dimensions = [d.__dict__() for d in measure_page.dimensions];
        return render_template('measure.html', topic=topic, measure_page=measure_page, dimensions=dimensions)


@static_site_blueprint.route('/<topic>/<subtopic>/measure-test/<measure>/<template_number>')
@login_required
def measure_page_test(topic, subtopic, measure, template_number):
        # don't care
        subtopic_guid = 'subtopic_%s' % subtopic
        measure_guid = page_service.get_measure_guid(subtopic_guid, measure)
        if measure_guid is None:
            abort(404)
        measure_page = page_service.get_page(measure_guid)
        template_name = 'measure_test_%s.html' % template_number

        return render_template(template_name, topic=topic, measure_page=measure_page)

