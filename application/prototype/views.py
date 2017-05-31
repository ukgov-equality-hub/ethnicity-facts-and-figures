import os
import csv
import yaml

from flask import (
    render_template,
    abort
)
from flask_login import login_required

from application.cms.utils import internal_user_required
from application.prototype import prototype_blueprint
from application.cms.page_service import page_service


@prototype_blueprint.route('/')
@internal_user_required
@login_required
def index():
    current_path = os.path.dirname(__file__)
    yaml_path = '%s/%s' % (current_path, 'data/copy/headline.yaml')
    with open(yaml_path, 'r') as yaml_file:
        data = yaml.load(yaml_file)

    return render_template('prototype/content.html', page=data)


# Add a static page
@prototype_blueprint.route('/contextual-analysis')
@internal_user_required
@login_required
def contextual_analysis():
    return render_template('prototype/contextual-analysis.html')


@prototype_blueprint.route('/<topic>')
@internal_user_required
@login_required
def topic(topic):
    if topic == 'private-life-and-community':
        guid = 'topic_%s' % topic.replace("-", "")
        page = page_service.get_page(guid)
        subtopics = page_service.get_subtopics(page)
        return render_template('prototype/topic.html', page=page, subtopics=subtopics)
    else:
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

        return render_template('prototype/old_topic.html', page=topic_data, data=data)


@prototype_blueprint.route('/<topic>/<subtopic>/measure/<measure>')
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

        return render_template('prototype/article_1.html', data=article_data, parent=parent_data, page=page_data)


@prototype_blueprint.route('/<topic>/<subtopic>/measure-test/<measure>/<template_number>')
@login_required
def measure_page_test(topic, subtopic, measure, template_number):
        subtopic_guid = 'subtopic_%s' % subtopic
        measure_guid = page_service.get_measure_guid(subtopic_guid, measure)
        if measure_guid is None:
            abort(404)
        measure_page = page_service.get_page(measure_guid)
        template_name = 'prototype/measure_test_%s.html' % template_number
        return render_template(template_name, topic=topic, measure_page=measure_page)
