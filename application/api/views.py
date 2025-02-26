import pathlib
from typing import List

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
from application.cms.models import user_measure, DataSource, Topic, Subtopic, Measure
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
    topics: List[Topic] = page_service.get_topics(include_testing_space=False)

    return jsonify({
        'urls': {
            'api': url_for('api.index', _external=True),
        },

        'topics': list(map(lambda topic: {
            'slug': topic.slug,
            'title': topic.title,
            'urls': urls_for_topic(topic),
        }, topics)),
    })


@api_blueprint.route("/<topic_slug>", methods=["GET"])
@auth.login_required
def topic_get(topic_slug):
    topic: Topic = page_service.get_topic_with_subtopics_and_measures(topic_slug)

    return jsonify({
        'slug': topic.slug,
        'title': topic.title,
        'short_title': topic.short_title,
        'description': topic.description,
        'additional_description': topic.additional_description,
        'meta_description': topic.meta_description,

        'urls': urls_for_topic(topic),

        'subtopics': list(map(lambda subtopic: {
            'slug': subtopic.slug,
            'title': subtopic.title,
            'position': subtopic.position,
            'urls': urls_for_subtopic(subtopic),
        }, sorted(topic.subtopics, key=lambda subtopic: subtopic.position))),
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>", methods=["GET"])
@auth.login_required
def subtopic_get(topic_slug, subtopic_slug):
    subtopic: Subtopic = page_service.get_subtopic(topic_slug, subtopic_slug)

    return jsonify({
        'slug': subtopic.slug,
        'title': subtopic.title,
        'position': subtopic.position,

        'urls': urls_for_subtopic(subtopic),

        'measures': list(map(lambda measure: {
            'slug': measure.slug,
            'position': measure.position,
            'retired': measure.retired,
            'urls': urls_for_measure(measure),
        }, sorted(subtopic.measures, key=lambda measure: measure.position))),

        'topic': {
            'slug': subtopic.topic.slug,
            'title': subtopic.topic.title,
            'urls': urls_for_topic(subtopic.topic),
        },
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>", methods=["GET"])
@auth.login_required
def measure_get(topic_slug, subtopic_slug, measure_slug):
    measure: Measure = page_service.get_measure(topic_slug, subtopic_slug, measure_slug)

    return jsonify({
        'slug': measure.slug,
        'position': measure.position,

        'urls': urls_for_measure(measure),

        'retired': measure.retired,
        'replaced_by_measure': ({
            'slug': measure.replaced_by_measure.slug,
            'urls': urls_for_measure(measure.replaced_by_measure),
        } if measure.replaced_by_measure is not None else None ),
        'replaces_measures': list(map(lambda replaces_measure: {
            'slug': replaces_measure.slug,
            'urls': urls_for_measure(replaces_measure),
        }, measure.replaces_measures)),

        'versions': {
            'all': list(map(lambda measure_version: {
                'version_ids': {
                    'version': measure_version.version,
                    'major': measure_version.major(),
                    'minor': measure_version.minor(),
                },
                'is_latest': measure_version.latest,
                'is_latest_published': measure_version.version == measure_version.measure.latest_published_version.version,
                'status': measure_version.status,
                'title': measure_version.title,
                'urls': urls_for_measure_version(measure_version),
            }, sorted(measure.versions, key=lambda measure_version: measure_version.version))),

            'latest_version': {
                'version_ids': {
                    'version': measure.latest_version.version,
                    'major': measure.latest_version.major(),
                    'minor': measure.latest_version.minor(),
                },
                'status': measure.latest_version.status,
                'title': measure.latest_version.title,
                'urls': urls_for_measure_version(measure.latest_version),
            },
            'latest_published_version': {
                'version_ids': {
                    'version': measure.latest_published_version.version,
                    'major': measure.latest_published_version.major(),
                    'minor': measure.latest_published_version.minor(),
                },
                'title': measure.latest_published_version.title,
                'urls': urls_for_measure_version(measure.latest_published_version),
            },
        },

        'subtopic': {
            'slug': measure.subtopic.slug,
            'title': measure.subtopic.title,
            'urls': urls_for_subtopic(measure.subtopic),
        },
        'topic': {
            'slug': measure.subtopic.topic.slug,
            'title': measure.subtopic.topic.title,
            'urls': urls_for_topic(measure.subtopic.topic),
        },
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>", methods=["GET"])
@auth.login_required
def measure_version_get(topic_slug, subtopic_slug, measure_slug, version):
    measure: Measure = page_service.get_measure(topic_slug, subtopic_slug, measure_slug)

    return jsonify({
    })


def urls_for_topic(topic):
    return {
        'api': url_for('api.topic_get', topic_slug=topic.slug, _external=True),
        'publisher': url_for('static_site.topic', topic_slug=topic.slug, _external=True),
        'public': f"{current_app.config.get('RDU_SITE')}{url_for('static_site.topic', topic_slug=topic.slug, _external=False)}",
    }


def urls_for_subtopic(subtopic):
    return {
        'api': url_for('api.subtopic_get', topic_slug=subtopic.topic.slug, subtopic_slug=subtopic.slug, _external=True),
        'publisher': f"{url_for('static_site.topic', topic_slug=subtopic.topic.slug, _external=True)}#accordion-{subtopic.slug}",
        'public': f"{current_app.config.get('RDU_SITE')}{url_for('static_site.topic', topic_slug=subtopic.topic.slug, _external=False)}#accordion-{subtopic.slug}",
    }


def urls_for_measure(measure):
    return {
        'api': url_for('api.measure_get', topic_slug=measure.subtopic.topic.slug, subtopic_slug=measure.subtopic.slug, measure_slug=measure.slug, _external=True),
        'publisher': url_for('static_site.measure_version', topic_slug=measure.subtopic.topic.slug, subtopic_slug=measure.subtopic.slug, measure_slug=measure.slug, version='latest', _external=True),
        'public': f"{current_app.config.get('RDU_SITE')}{url_for('static_site.measure_version', topic_slug=measure.subtopic.topic.slug, subtopic_slug=measure.subtopic.slug, measure_slug=measure.slug, version='latest', _external=False)}",
    }


def urls_for_measure_version(measure_version):
    return {
        'api': url_for('api.measure_version_get', topic_slug=measure_version.measure.subtopic.topic.slug, subtopic_slug=measure_version.measure.subtopic.slug, measure_slug=measure_version.measure.slug, version=measure_version.version, _external=True),
        'publisher': url_for('static_site.measure_version', topic_slug=measure_version.measure.subtopic.topic.slug, subtopic_slug=measure_version.measure.subtopic.slug, measure_slug=measure_version.measure.slug, version=measure_version.version, _external=True),
        'public': f"{current_app.config.get('RDU_SITE')}{url_for('static_site.measure_version', topic_slug=measure_version.measure.subtopic.topic.slug, subtopic_slug=measure_version.measure.subtopic.slug, measure_slug=measure_version.measure.slug, version=measure_version.version, _external=False)}",
    }
