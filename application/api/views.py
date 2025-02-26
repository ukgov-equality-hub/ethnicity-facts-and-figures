import pathlib
from flask import abort, current_app, flash, redirect, render_template, request, url_for, jsonify
from flask_login import login_required, current_user
from flask_httpauth import HTTPTokenAuth
from sqlalchemy import desc, func
from sqlalchemy.orm.exc import NoResultFound
from datetime import date, datetime, timedelta

from application import db
from application.api import api_blueprint
from application.admin.forms import AddUserForm, SiteBuildSearchForm, DataSourceSearchForm, DataSourceMergeForm
from application.auth.models import (
    User,
    TypeOfUser,
    CAPABILITIES,
    MANAGE_SYSTEM,
    MANAGE_USERS,
    MANAGE_DATA_SOURCES,
    MANAGE_TOPICS,
)
from application.cms.forms import SelectMultipleDataSourcesForm
from application.cms.models import user_measure, DataSource, Topic, Subtopic
from application.sitebuilder.models import Build, BuildStatus
from application.cms.page_service import page_service
from application.utils import create_and_send_activation_email, user_can
from application.cms.utils import get_form_errors


auth = HTTPTokenAuth(scheme='Bearer')

@auth.verify_token
def verify_token(token):
    if current_app.config.get('EFF_API_TOKEN') is None:
        return False

    return token == current_app.config.get('EFF_API_TOKEN')


@api_blueprint.route("/", methods=["GET"])
@auth.login_required
def index():
    topics = page_service.get_topics(include_testing_space=False)

    return jsonify({
        'api_url': url_for('api.index', _external=True),

        'topics': list(map(lambda topic: {
            'slug': topic.slug,
            'title': topic.title,
            'api_url': url_for('api.topic_get', topic_slug=topic.slug, _external=True),
            'publisher_url': url_for('static_site.topic', topic_slug=topic.slug, _external=True),
        }, topics)),
    })


@api_blueprint.route("/<topic_slug>", methods=["GET"])
@auth.login_required
def topic_get(topic_slug):
    topic = page_service.get_topic_with_subtopics_and_measures(topic_slug)

    return jsonify({
        'slug': topic.slug,
        'title': topic.title,
        'short_title': topic.short_title,
        'description': topic.description,
        'additional_description': topic.additional_description,
        'meta_description': topic.meta_description,

        'api_url': url_for('api.topic_get', topic_slug=topic.slug, _external=True),
        'publisher_url': url_for('static_site.topic', topic_slug=topic.slug, _external=True),

        'subtopics': list(map(lambda subtopic: {
            'slug': subtopic.slug,
            'title': subtopic.title,
            'position': subtopic.position,
            'api_url': url_for('api.subtopic_get', topic_slug=topic.slug, subtopic_slug=subtopic.slug, _external=True),
            'publisher_url': f"{url_for('static_site.topic', topic_slug=topic.slug, _external=True)}##accordion-{subtopic.slug}",
        }, sorted(topic.subtopics, key=lambda subtopic: subtopic.position))),
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>", methods=["GET"])
@auth.login_required
def subtopic_get(topic_slug, subtopic_slug):
    subtopic = page_service.get_subtopic(topic_slug, subtopic_slug)

    return jsonify({
        'slug': subtopic.slug,
        'title': subtopic.title,
        'position': subtopic.position,

        'measures': list(map(lambda measure: {
            'slug': measure.slug,
            'position': measure.position,
            'retired': measure.retired,
            'api_url': url_for('api.measure_get', topic_slug=subtopic.topic.slug, subtopic_slug=subtopic.slug, measure_slug=measure.slug, _external=True),
        }, sorted(subtopic.measures, key=lambda measure: measure.position))),

        'topic': {
            'slug': subtopic.topic.slug,
            'title': subtopic.topic.title,
            'api_url': url_for('api.topic_get', topic_slug=subtopic.topic.slug, _external=True),
        },
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>", methods=["GET"])
@auth.login_required
def measure_get(topic_slug, subtopic_slug, measure_slug):
    measure = page_service.get_measure(topic_slug, subtopic_slug, measure_slug)

    return jsonify({
        'slug': measure.slug,
        'position': measure.position,

        'retired': measure.retired,
        'replaced_by_measure': ({
            'slug': measure.replaced_by_measure.slug,
            'api_url': url_for('api.measure_get', topic_slug=measure.replaced_by_measure.subtopic.topic.slug, subtopic_slug=measure.replaced_by_measure.subtopic.slug, measure_slug=measure.replaced_by_measure.slug, _external=True),
        } if measure.replaced_by_measure is not None else None ),
        'replaces_measures': list(map(lambda replaces_measure: {
            'slug': replaces_measure.slug,
            'api_url': url_for('api.measure_get', topic_slug=replaces_measure.subtopic.topic.slug, subtopic_slug=replaces_measure.subtopic.slug, measure_slug=replaces_measure.slug, _external=True),
        }, measure.replaces_measures)),

        # 'measures': list(map(lambda measure: {
        #     'slug': measure.slug,
        #     'position': measure.position,
        #     'api_url': url_for('api.measure_get', topic_slug=subtopic.topic.slug, subtopic_slug=subtopic.slug, measure_slug=measure.slug, _external=True),
        # }, sorted(subtopic.measures, key=lambda measure: measure.position))),

        'subtopic': {
            'slug': measure.subtopic.slug,
            'title': measure.subtopic.title,
            'api_url': url_for('api.subtopic_get', topic_slug=measure.subtopic.topic.slug, subtopic_slug=measure.subtopic.slug, _external=True),
        },
        'topic': {
            'slug': measure.subtopic.topic.slug,
            'title': measure.subtopic.topic.title,
            'api_url': url_for('api.topic_get', topic_slug=measure.subtopic.topic.slug, _external=True),
        },
    })
