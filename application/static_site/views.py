import os
import json
import csv
import yaml


from flask import render_template, current_app
from flask_login import login_required
from application.static_site import static_site_blueprint


@static_site_blueprint.route('/')
@login_required
def index():
    # temporarily load some data from yaml
    current_path = os.path.dirname(__file__)
    yaml_path = '%s/%s' % (current_path, 'data/copy/headline.yaml')
    with open(yaml_path, 'r') as yaml_file:
        data = yaml.load(yaml_file)

    return render_template('content.html', page=data)


@static_site_blueprint.route('/<topic>')
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
        repo_path = current_app.config['REPO_DIR']
        page_path = '%s/content/topic_%s/subtopic_%s/%s/page.json' % (repo_path, topic, subtopic, measure)
        with open(page_path) as page_file:
            page_data = json.loads(page_file.read())

        meta_path = '%s/content/topic_%s/subtopic_%s/%s/meta.json' % (repo_path, topic, subtopic, measure)
        with open(meta_path) as meta_file:
            metadata = json.loads(meta_file.read())

    return render_template('article.html', **page_data)
