import os
import pathlib
from tempfile import NamedTemporaryFile
from typing import List

from botocore.exceptions import ClientError
from flask import abort, current_app, flash, redirect, render_template, request, url_for, jsonify, send_file
from flask_login import login_required, current_user
from flask_httpauth import HTTPTokenAuth
from slugify import slugify
from sqlalchemy import desc, func
from sqlalchemy.orm.exc import NoResultFound
from datetime import date, datetime, timedelta

from application import db, csrf
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
from application.cms.exceptions import UploadNotFoundException
from application.cms.forms import SelectMultipleDataSourcesForm
from application.cms.models import user_measure, DataSource, Topic, Subtopic, Measure, MeasureVersion, NewVersionType, \
    Dimension, Upload
from application.cms.upload_service import upload_service
from application.sitebuilder.models import Build, BuildStatus
from application.cms.page_service import page_service
from application.utils import create_and_send_activation_email, user_can, get_csv_data_for_download
from application.cms.utils import get_form_errors

auth = HTTPTokenAuth(scheme='Bearer')


@auth.verify_token
def verify_token(token: str) -> bool:
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


@api_blueprint.route("/data-sources", methods=["GET"])
@auth.login_required
def data_sources_get():
    data_sources: List[DataSource] = DataSource.query.order_by(DataSource.id).all()

    return jsonify({
        'data_sources': list(map(lambda data_source: get_data_source_json(data_source), data_sources)),

        'urls': {
            'api': url_for('api.data_sources_get', _external=True),
            'publisher': url_for('admin.data_sources', _external=True),
        },
    })


@api_blueprint.route("/data-sources/<data_source_id>", methods=["GET"])
@auth.login_required
def data_source_get(data_source_id: int):
    data_source: DataSource = DataSource.query.get(data_source_id)

    return jsonify(get_data_source_json(data_source))


def get_data_source_json(data_source: DataSource):
    return {
        'id': data_source.id,

        'source_url': data_source.source_url,
        'title': data_source.title,

        'publisher': ({
            'id': data_source.publisher.id,
            'name': data_source.publisher.name,
        } if data_source.publisher else None),

        'publication_date': data_source.publication_date,

        'frequency_of_release': ({
            'id': data_source.frequency_of_release.id,
            'description': data_source.frequency_of_release.description,
            'other': data_source.frequency_of_release_other,
        } if data_source.frequency_of_release else None),

        'type_of_data': list(map(lambda type_of_data: type_of_data.name, data_source.type_of_data)),

        'type_of_statistic': ({
            'id': data_source.type_of_statistic.id,
            'internal': data_source.type_of_statistic.internal,
            'external': data_source.type_of_statistic.external,
        } if data_source.type_of_statistic else None),

        'urls': urls_for_data_source(data_source),
    }


@api_blueprint.route("/<topic_slug>", methods=["GET"])
@auth.login_required
def topic_get(topic_slug: str):
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
def subtopic_get(topic_slug: str, subtopic_slug: str):
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

        'parent_entities': {
            'topic': topic_summary(subtopic.topic),
        },
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>", methods=["GET"])
@auth.login_required
def measure_get(topic_slug: str, subtopic_slug: str, measure_slug: str):
    measure: Measure = page_service.get_measure(topic_slug, subtopic_slug, measure_slug)

    next_major_version_id: str = measure.latest_published_version.next_major_version()
    next_major_version: MeasureVersion = next(filter(lambda measure_version: measure_version.version == next_major_version_id, measure.versions), None)

    next_minor_version_id: str = measure.latest_published_version.next_minor_version()
    next_minor_version: MeasureVersion = next(filter(lambda measure_version: measure_version.version == next_minor_version_id, measure.versions), None)

    def add_url_for_create_next_version_post(urls, major_or_minor: str):
        urls['create_next_version_POST'] =\
            url_for('api.measure_next_version_post',
                    topic_slug=topic_slug,
                    subtopic_slug=subtopic_slug,
                    measure_slug=measure_slug,
                    major_or_minor=major_or_minor,
                    _external=True)
        return urls

    return jsonify({
        'slug': measure.slug,
        'position': measure.position,

        'urls': urls_for_measure(measure),

        'retired': measure.retired,
        'replaced_by_measure': ({
                                    'slug': measure.replaced_by_measure.slug,
                                    'urls': urls_for_measure(measure.replaced_by_measure),
                                } if measure.replaced_by_measure is not None else None),
        'replaces_measures': list(map(lambda replaces_measure: {
            'slug': replaces_measure.slug,
            'urls': urls_for_measure(replaces_measure),
        }, measure.replaces_measures)),

        'versions': {
            'all': list(map(lambda measure_version: {
                'version_ids': version_ids_for_measure_version(measure_version),
                'is_latest': measure_version.latest,
                'is_latest_published': measure_version.version == measure_version.measure.latest_published_version.version,
                'status': measure_version.status,
                'title': measure_version.title,
                'urls': urls_for_measure_version(measure_version),
            }, sorted(measure.versions, key=lambda measure_version: measure_version.version))),

            'latest_version': {
                'version_ids': version_ids_for_measure_version(measure.latest_version),
                'status': measure.latest_version.status,
                'title': measure.latest_version.title,
                'urls': urls_for_measure_version(measure.latest_version),
            },
            'latest_published_version': {
                'version_ids': version_ids_for_measure_version(measure.latest_published_version),
                'title': measure.latest_published_version.title,
                'urls': urls_for_measure_version(measure.latest_published_version),
            },

            'next_or_draft': {
                'major': {
                    'version': next_major_version_id,
                    'exists': next_major_version is not None,
                    'urls': add_url_for_create_next_version_post(
                        urls_for_measure_version(next_major_version) if next_major_version is not None else {},
                        'major')
                },
                'minor': {
                    'version': next_minor_version_id,
                    'exists': next_minor_version is not None,
                    'urls': add_url_for_create_next_version_post(
                        urls_for_measure_version(next_minor_version) if next_minor_version is not None else {},
                        'minor')
                },
            },
        },

        'parent_entities': {
            'subtopic': subtopic_summary(measure.subtopic),
            'topic': topic_summary(measure.topic),
        },
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/next-or-draft/<major_or_minor>", methods=["POST"])
@csrf.exempt
@auth.login_required
def measure_next_version_post(topic_slug: str, subtopic_slug: str, measure_slug: str, major_or_minor: str):
    # Check that the measure is valid first, before checking major_or_minor
    measure: Measure = page_service.get_measure(topic_slug, subtopic_slug, measure_slug)

    if major_or_minor not in ["major", "minor"]:
        return jsonify({
            'error': "Invalid URL - the last component (major_or_minor) must be either 'major' or 'minor'",
            'major_or_minor': major_or_minor,
            'request_url': request.url,
            'valid_urls': {
                'major': url_for('api.measure_next_version_post',
                                 topic_slug=topic_slug,
                                 subtopic_slug=subtopic_slug,
                                 measure_slug=measure_slug,
                                 major_or_minor="major"),
                'minor': url_for('api.measure_next_version_post',
                                 topic_slug=topic_slug,
                                 subtopic_slug=subtopic_slug,
                                 measure_slug=measure_slug,
                                 major_or_minor="minor"),
            },
        }), 400

    latest_published_version: MeasureVersion = measure.latest_published_version
    next_version_id: str = latest_published_version.next_major_version() if major_or_minor == "major" else latest_published_version.next_minor_version()

    new_measure_version: MeasureVersion = next(filter(lambda measure_version: measure_version.version == next_version_id, measure.versions), None)

    if new_measure_version is None:
        new_measure_version = page_service.create_measure_version(latest_published_version, NewVersionType(major_or_minor), user=None, created_by_api=True)

    return jsonify({
        'version_ids': {
            'version': new_measure_version.version,
            'major': new_measure_version.major(),
            'minor': new_measure_version.minor(),
        },
        'status': new_measure_version.status,
        'urls': urls_for_measure_version(new_measure_version),
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>", methods=["GET"])
@auth.login_required
def measure_version_get(topic_slug, subtopic_slug, measure_slug, version):
    measure_version: MeasureVersion = page_service.get_measure_version(topic_slug, subtopic_slug, measure_slug, version)

    def add_url_publisher_data_source_edit(urls, data_source_id: int):
        urls['publisher'] = url_for('cms.update_data_source',
                                    topic_slug=topic_slug,
                                    subtopic_slug=subtopic_slug,
                                    measure_slug=measure_slug,
                                    version=version,
                                    data_source_id=data_source_id,
                                    _external=True)
        return urls

    return jsonify({
        'template_version': measure_version.template_version,

        'title': measure_version.title,
        'description': measure_version.description,
        'time_covered': measure_version.time_covered,

        'geography': {
            'area_covered': list(map(lambda area_covered: area_covered.name, measure_version.area_covered)),
            'lowest_level_of_geography': measure_version.lowest_level_of_geography.name,
        },

        'commentary': {
            'summary': measure_version.summary,
            'need_to_know': measure_version.need_to_know,
            'measure_summary': measure_version.measure_summary,
            'ethnicity_definition_summary': measure_version.ethnicity_definition_summary,
        },

        'methodology': {
            'methodology': measure_version.methodology,
            'suppression_and_disclosure': measure_version.suppression_and_disclosure,
            'estimation': measure_version.estimation,
            'related_publications': measure_version.related_publications,
            'quality_methodology_information_url': measure_version.qmi_url,
            'further_technical_information': measure_version.further_technical_information,
        },

        'updates_and_corrections': {
            'update_corrects_data_mistake': measure_version.update_corrects_data_mistake,
            'external_edit_summary': measure_version.external_edit_summary,
            'internal_edit_summary': measure_version.internal_edit_summary,
        },

        'data_sources': list(map(lambda data_source: {
            'id': data_source.id,
            'title': data_source.title,
            'urls': add_url_publisher_data_source_edit(urls_for_data_source(data_source), data_source.id),
        }, measure_version.data_sources)),

        'dimensions': list(map(lambda dimension: {
            'guid': dimension.guid,
            'title': dimension.title,
            'urls': urls_for_dimension(dimension),
        }, sorted(measure_version.dimensions, key=lambda dimension: dimension.position))),

        'data_uploads': list(map(lambda upload: {
            'guid': upload.guid,
            'title': upload.title,
            'file_name': upload.file_name,
            'description': upload.description,
            'size': upload.size,
            'urls': urls_for_data_upload(upload),
        }, measure_version.uploads)),

        'status': measure_version.status,
        'is_latest': measure_version.latest,
        'is_latest_published': measure_version.version == measure_version.measure.latest_published_version.version,

        'version_ids': version_ids_for_measure_version(measure_version),
        'urls': urls_for_measure_version(measure_version),

        'parent_entities': {
            'measure': measure_summary(measure_version.measure),
            'subtopic': subtopic_summary(measure_version.measure.subtopic),
            'topic': topic_summary(measure_version.measure.subtopic.topic),
        },
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/uploads/<upload_guid>", methods=["GET"])
@auth.login_required
def upload_get(topic_slug, subtopic_slug, measure_slug, version, upload_guid):
    upload: Upload = page_service.get_upload(
        topic_slug, subtopic_slug, measure_slug, version, upload_guid
    )

    return jsonify({
        'guid': upload.guid,
        'title': upload.title,
        'file_name': upload.file_name,
        'description': upload.description,
        'size': upload.size,

        'urls': urls_for_data_upload(upload),

        'parent_entities': {
            'measure_version': measure_version_summary(upload.measure_version),
            'measure': measure_summary(upload.measure_version.measure),
            'subtopic': subtopic_summary(upload.measure_version.measure.subtopic),
            'topic': topic_summary(upload.measure_version.measure.subtopic.topic),
        },
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/uploads/<upload_guid>/download-file", methods=["GET"])
@auth.login_required
def upload_file_download(topic_slug, subtopic_slug, measure_slug, version, upload_guid):
    try:
        measure_version: MeasureVersion = page_service.get_measure_version(
            topic_slug, subtopic_slug, measure_slug, version
        )
        upload: Upload = next(filter(lambda upload: upload.guid == upload_guid, measure_version.uploads), None)
        downloaded_filename: str = upload_service.get_measure_download(upload, upload.file_name, "source")
        content: str = get_csv_data_for_download(downloaded_filename)
        if os.path.exists(downloaded_filename):
            os.remove(downloaded_filename)
        if content.strip() == "":
            abort(404)

        outfile = NamedTemporaryFile("w", encoding="windows-1252", delete=False)
        outfile.write(content)
        outfile.flush()

        return send_file(outfile.name, as_attachment=True, mimetype="text/csv", attachment_filename=upload.file_name)

    except (UploadNotFoundException, FileNotFoundError, ClientError):
        abort(404)


@api_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>", methods=["GET"])
@auth.login_required
def dimension_get(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    measure_version: MeasureVersion = page_service.get_measure_version(topic_slug, subtopic_slug, measure_slug, version)
    dimension: Dimension = next(filter(lambda dimension: dimension.guid == dimension_guid, measure_version.dimensions), None)

    return jsonify({
        'guid': dimension.guid,
        'position': dimension.position,

        'title': dimension.title,
        'time_period': dimension.time_period,
        'summary': dimension.summary,

        'chart': {
            'exists': dimension.dimension_chart is not None,
            'urls': urls_for_dimension_chart(dimension),
        },
        'table': {
            'exists': dimension.dimension_table is not None,
            'urls': urls_for_dimension_table(dimension),
        },

        # Data Classification
        # TODO

        'urls': urls_for_dimension(dimension),

        'parent_entities': {
            'measure_version': measure_version_summary(dimension.measure_version),
            'measure': measure_summary(dimension.measure_version.measure),
            'subtopic': subtopic_summary(dimension.measure_version.measure.subtopic),
            'topic': topic_summary(dimension.measure_version.measure.subtopic.topic),
        },
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/chart", methods=["GET"])
@auth.login_required
def dimension_chart_get(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    measure_version: MeasureVersion = page_service.get_measure_version(topic_slug, subtopic_slug, measure_slug, version)
    dimension: Dimension = next(filter(lambda dimension: dimension.guid == dimension_guid, measure_version.dimensions), None)

    if not dimension.dimension_chart:
        abort(404)

    return jsonify({
        'ethnicity_classification': {
            'classification_id': dimension.dimension_chart.classification_id,
            'classification_title': (dimension.dimension_chart.classification.title
                                     if dimension.dimension_chart.classification
                                     else None),
            'includes_parents': dimension.dimension_chart.includes_parents,
            'includes_all': dimension.dimension_chart.includes_all,
            'includes_unknown': dimension.dimension_chart.includes_unknown,
        },

        'settings_and_source_data': dimension.dimension_chart.settings_and_source_data,
        'chart_object': dimension.dimension_chart.chart_object,

        'urls': urls_for_dimension_chart(dimension),

        'parent_entities': {
            'dimension': dimension_summary(dimension),
            'measure_version': measure_version_summary(dimension.measure_version),
            'measure': measure_summary(dimension.measure_version.measure),
            'subtopic': subtopic_summary(dimension.measure_version.measure.subtopic),
            'topic': topic_summary(dimension.measure_version.measure.subtopic.topic),
        },
    })


@api_blueprint.route("/<topic_slug>/<subtopic_slug>/<measure_slug>/<version>/<dimension_guid>/table", methods=["GET"])
@auth.login_required
def dimension_table_get(topic_slug, subtopic_slug, measure_slug, version, dimension_guid):
    measure_version: MeasureVersion = page_service.get_measure_version(topic_slug, subtopic_slug, measure_slug, version)
    dimension: Dimension = next(filter(lambda dimension: dimension.guid == dimension_guid, measure_version.dimensions), None)

    if not dimension.dimension_table:
        abort(404)

    return jsonify({
        'ethnicity_classification': {
            'classification_id': dimension.dimension_table.classification_id,
            'classification_title': (dimension.dimension_table.classification.title
                                     if dimension.dimension_table.classification
                                     else None),
            'includes_parents': dimension.dimension_table.includes_parents,
            'includes_all': dimension.dimension_table.includes_all,
            'includes_unknown': dimension.dimension_table.includes_unknown,
        },

        'settings_and_source_data': dimension.dimension_table.settings_and_source_data,
        'table_object': dimension.dimension_table.table_object,

        'urls': urls_for_dimension_table(dimension),

        'parent_entities': {
            'dimension': dimension_summary(dimension),
            'measure_version': measure_version_summary(dimension.measure_version),
            'measure': measure_summary(dimension.measure_version.measure),
            'subtopic': subtopic_summary(dimension.measure_version.measure.subtopic),
            'topic': topic_summary(dimension.measure_version.measure.subtopic.topic),
        },
    })


def topic_summary(topic: Topic):
    return {
        'slug': topic.slug,
        'title': topic.title,
        'urls': urls_for_topic(topic),
    }


def subtopic_summary(subtopic: Subtopic):
    return {
        'slug': subtopic.slug,
        'title': subtopic.title,
        'urls': urls_for_subtopic(subtopic),
    }


def measure_summary(measure: Measure):
    return {
        'slug': measure.slug,
        'urls': urls_for_measure(measure),
    }


def measure_version_summary(measure_version: MeasureVersion):
    return {
        'version_ids': version_ids_for_measure_version(measure_version),
        'slug': measure_version.measure.slug,
        'urls': urls_for_measure_version(measure_version),
    }


def dimension_summary(dimension: Dimension):
    return {
        'guid': dimension.guid,
        'title': dimension.title,
        'urls': urls_for_dimension(dimension),
    }


def version_ids_for_measure_version(measure_version: MeasureVersion):
    return {
        'version': measure_version.version,
        'major': measure_version.major(),
        'minor': measure_version.minor(),
    }


def urls_for_topic(topic: Topic):
    return {
        'api':
            url_for('api.topic_get',
                    topic_slug=topic.slug,
                    _external=True),
        'publisher':
            url_for('static_site.topic',
                    topic_slug=topic.slug,
                    _external=True),
        'public':
            current_app.config.get('RDU_SITE') +
            url_for('static_site.topic',
                    topic_slug=topic.slug,
                    _external=False),
    }


def urls_for_subtopic(subtopic: Subtopic):
    return {
        'api':
            url_for('api.subtopic_get',
                    topic_slug=subtopic.topic.slug,
                    subtopic_slug=subtopic.slug,
                    _external=True),
        'publisher':
            url_for('static_site.topic',
                    topic_slug=subtopic.topic.slug,
                    _external=True) +
            f"#accordion-{subtopic.slug}",
        'public':
            current_app.config.get('RDU_SITE') +
            url_for('static_site.topic',
                    topic_slug=subtopic.topic.slug,
                    _external=False) +
            "#accordion-" +
            subtopic.slug,
    }


def urls_for_measure(measure: Measure):
    return {
        'api':
            url_for('api.measure_get',
                    topic_slug=measure.subtopic.topic.slug,
                    subtopic_slug=measure.subtopic.slug,
                    measure_slug=measure.slug,
                    _external=True),
        'publisher':
            url_for('static_site.measure_version',
                    topic_slug=measure.subtopic.topic.slug,
                    subtopic_slug=measure.subtopic.slug,
                    measure_slug=measure.slug,
                    version='latest',
                    _external=True),
        'public':
            current_app.config.get('RDU_SITE') +
            url_for('static_site.measure_version',
                    topic_slug=measure.subtopic.topic.slug,
                    subtopic_slug=measure.subtopic.slug,
                    measure_slug=measure.slug,
                    version='latest',
                    _external=False),
    }


def urls_for_measure_version(measure_version: MeasureVersion):
    return {
        'api':
            url_for('api.measure_version_get',
                    topic_slug=measure_version.measure.subtopic.topic.slug,
                    subtopic_slug=measure_version.measure.subtopic.slug,
                    measure_slug=measure_version.measure.slug,
                    version=measure_version.version,
                    _external=True),
        'publisher':
            url_for('static_site.measure_version',
                    topic_slug=measure_version.measure.subtopic.topic.slug,
                    subtopic_slug=measure_version.measure.subtopic.slug,
                    measure_slug=measure_version.measure.slug,
                    version=measure_version.version,
                    _external=True),
        'public':
            current_app.config.get('RDU_SITE') +
            url_for('static_site.measure_version',
                    topic_slug=measure_version.measure.subtopic.topic.slug,
                    subtopic_slug=measure_version.measure.subtopic.slug,
                    measure_slug=measure_version.measure.slug,
                    version=measure_version.version,
                    _external=False),
    }


def urls_for_data_source(data_source):
    return {
        'api': url_for('api.data_source_get', data_source_id=data_source.id, _external=True),
    }


def urls_for_dimension(dimension: Dimension):
    return {
        'api':
            url_for('api.dimension_get',
                    topic_slug=dimension.measure_version.measure.subtopic.topic.slug,
                    subtopic_slug=dimension.measure_version.measure.subtopic.slug,
                    measure_slug=dimension.measure_version.measure.slug,
                    version=dimension.measure_version.version,
                    dimension_guid=dimension.guid,
                    _external=True),
        'publisher':
            url_for('cms.edit_dimension',
                    topic_slug=dimension.measure_version.measure.subtopic.topic.slug,
                    subtopic_slug=dimension.measure_version.measure.subtopic.slug,
                    measure_slug=dimension.measure_version.measure.slug,
                    version=dimension.measure_version.version,
                    dimension_guid=dimension.guid,
                    _external=True),
        'public':
            current_app.config.get('RDU_SITE') +
            url_for('static_site.measure_version',
                    topic_slug=dimension.measure_version.measure.subtopic.topic.slug,
                    subtopic_slug=dimension.measure_version.measure.subtopic.slug,
                    measure_slug=dimension.measure_version.measure.slug,
                    version=dimension.measure_version.version,
                    _external=False) +
            "#" +
            slugify(dimension.title),
    }


def urls_for_data_upload(upload: Upload):
    return {
        'api':
            url_for('api.upload_get',
                    topic_slug=upload.measure_version.measure.subtopic.topic.slug,
                    subtopic_slug=upload.measure_version.measure.subtopic.slug,
                    measure_slug=upload.measure_version.measure.slug,
                    version=upload.measure_version.version,
                    upload_guid=upload.guid,
                    _external=True),
        'api_download':
            url_for('api.upload_file_download',
                    topic_slug=upload.measure_version.measure.subtopic.topic.slug,
                    subtopic_slug=upload.measure_version.measure.subtopic.slug,
                    measure_slug=upload.measure_version.measure.slug,
                    version=upload.measure_version.version,
                    upload_guid=upload.guid,
                    _external=True),
        'publisher_edit':
            url_for('cms.edit_upload',
                    topic_slug=upload.measure_version.measure.subtopic.topic.slug,
                    subtopic_slug=upload.measure_version.measure.subtopic.slug,
                    measure_slug=upload.measure_version.measure.slug,
                    version=upload.measure_version.version,
                    upload_guid=upload.guid,
                    _external=True),
        'publisher_download':
            url_for('static_site.measure_version_file_download',
                    topic_slug=upload.measure_version.measure.subtopic.topic.slug,
                    subtopic_slug=upload.measure_version.measure.subtopic.slug,
                    measure_slug=upload.measure_version.measure.slug,
                    version=upload.measure_version.version,
                    filename=upload.file_name,
                    _external=True),
        'public':
            current_app.config.get('RDU_SITE') +
            url_for('static_site.measure_version_file_download',
                    topic_slug=upload.measure_version.measure.subtopic.topic.slug,
                    subtopic_slug=upload.measure_version.measure.subtopic.slug,
                    measure_slug=upload.measure_version.measure.slug,
                    version=upload.measure_version.version,
                    filename=upload.file_name,
                    _external=False),
    }


def urls_for_dimension_chart(dimension: Dimension):
    return {
        'api': url_for('api.dimension_chart_get',
                       topic_slug=dimension.measure_version.measure.subtopic.topic.slug,
                       subtopic_slug=dimension.measure_version.measure.subtopic.slug,
                       measure_slug=dimension.measure_version.measure.slug,
                       version=dimension.measure_version.version,
                       dimension_guid=dimension.guid,
                       _external=True),
    }


def urls_for_dimension_table(dimension: Dimension):
    return {
        'api': url_for('api.dimension_table_get',
                       topic_slug=dimension.measure_version.measure.subtopic.topic.slug,
                       subtopic_slug=dimension.measure_version.measure.subtopic.slug,
                       measure_slug=dimension.measure_version.measure.slug,
                       version=dimension.measure_version.version,
                       dimension_guid=dimension.guid,
                       _external=True),
    }
