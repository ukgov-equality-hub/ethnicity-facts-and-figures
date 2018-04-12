import calendar
from datetime import date, timedelta, datetime

from flask import render_template, jsonify, url_for
from flask_login import login_required
from slugify import slugify
from sqlalchemy import not_
from sqlalchemy.orm import joinedload

from application.dashboard.queries import query_dimensions_with_categorisation_link_to_value, \
    query_dimensions_with_categorisation_link_to_values
from sqlalchemy import not_, PrimaryKeyConstraint, UniqueConstraint

from application import db
from application.factory import page_service

from application.dashboard import dashboard_blueprint
from application.cms.categorisation_service import categorisation_service
from application.utils import internal_user_required

from application.cms.models import Page, DimensionCategorisation


def page_in_week(page, week):
    return page.publication_date >= week[0] and page.publication_date <= week[6]


@dashboard_blueprint.route('/')
@internal_user_required
@login_required
def index():
    original_publications = Page.query.filter(Page.publication_date.isnot(None),
                                              Page.version == '1.0',
                                              Page.page_type == 'measure').order_by(Page.publication_date.desc()).all()

    major_updates = Page.query.filter(Page.publication_date.isnot(None),
                                      Page.page_type == 'measure',
                                      not_(Page.version.startswith('1'))) \
        .order_by(Page.publication_date.desc()).all()

    first_publication = Page.query.filter(
        Page.publication_date.isnot(None)
    ).order_by(Page.publication_date.asc()).first()

    data = {'number_of_publications': len(original_publications),
            'number_of_major_updates': len(major_updates),
            'first_publication': first_publication.publication_date}

    weeks = []
    cumulative_total = []

    for d in _from_month_to_month(first_publication.publication_date, date.today()):
        c = calendar.Calendar(calendar.MONDAY).monthdatescalendar(d.year, d.month)
        for week in c:
            if _in_range(week, first_publication.publication_date, d.month):

                publications = [page for page in original_publications if page_in_week(page, week)]
                updates = [updated_page for updated_page in major_updates if page_in_week(updated_page, week)]
                weeks.append({'week': week[0],
                              'publications': publications,
                              'major_updates': updates})

                if not cumulative_total:
                    cumulative_total.append(len(publications) + len(updates))
                else:
                    last_total = cumulative_total[-1]
                    cumulative_total.append(last_total + len(publications) + len(updates))
    weeks.reverse()
    data['weeks'] = weeks
    data['graph_values'] = cumulative_total

    return render_template('dashboard/index.html', data=data)


@dashboard_blueprint.route('/measures')
@internal_user_required
@login_required
def measures():
    pages = page_service.get_pages_by_type('topic')
    return render_template('dashboard/measures.html', pages=pages)


@dashboard_blueprint.route('/ethnic-groups')
@internal_user_required
@login_required
def ethnic_groups():
    links = EthnicGroupByDimension.query.order_by(
        EthnicGroupByDimension.subtopic_guid, EthnicGroupByDimension.page_position,
        EthnicGroupByDimension.dimension_position, EthnicGroupByDimension.value_position).all()

    # build a data structure with the links to count unique
    ethnicities = {}
    for link in links:
        if link.value not in ethnicities:
            ethnicities[link.value] = {'value': link.value,
                                       'position': link.value_position,
                                       'url': url_for("dashboard.ethnic_group", value_uri=slugify(link.value)),
                                       'pages': {link.page_guid},
                                       'dimensions': 1,
                                       'categorisations': {link.categorisation}}
        else:
            ethnicities[link.value]['dimensions'] += 1
            ethnicities[link.value]['pages'].add(link.page_guid)
            ethnicities[link.value]['categorisations'].add(link.categorisation)
    for ethnic_group in ethnicities.values():
        ethnic_group['pages'] = len(ethnic_group['pages'])
        ethnic_group['categorisations'] = len(ethnic_group['categorisations'])

    # sort by standard ethnicity position
    sorted_ethnicity_list = sorted(ethnicities.values(), key=lambda g: g['position'])

    return render_template('dashboard/ethnicity_values.html', ethnic_groups=sorted_ethnicity_list)


@dashboard_blueprint.route('/ethnicity-categorisations')
@internal_user_required
@login_required
def ethnicity_categorisations():
    categorisations = categorisation_service.get_all_categorisations_with_counts()

    categorisations_with_parents = [categorisation.title for
                                    categorisation in categorisation_service.get_all_categorisations()
                                    if len(categorisation.parent_values) > 0]

    return render_template('dashboard/ethnicity_categorisations.html',
                           ethnicity_categorisations=categorisations,
                           categorisations_with_parents=categorisations_with_parents)


@dashboard_blueprint.route('/ethnicity-categorisations/<categorisation_id>')
@internal_user_required
@login_required
def ethnicity_categorisation(categorisation_id):
    categorisation = categorisation_service.get_categorisation_by_id(categorisation_id)

    # get pages
    pages = {link.dimension.page_id: {
        'measure': link.dimension.page.title,
        'measure_order': link.dimension.page.position,
        'measure_url': url_for("static_site.measure_page",
                               topic=link.dimension.page.parent.parent.uri,
                               subtopic=link.dimension.page.parent.uri,
                               measure=link.dimension.page.uri,
                               version=link.dimension.page.version),
        'subtopic': link.dimension.page.parent.title,
        'subtopic_order': link.dimension.page.parent.position,
        'topic': link.dimension.page.parent.parent.title,
        'topic_order': link.dimension.page.parent.parent.position,
        'dimensions': []
    } for link in categorisation.dimension_links if link.dimension.page.latest}

    # add dimensions to pages
    for dimension_link in categorisation.dimension_links:
        dimension = dimension_link.dimension
        if dimension.page.latest:
            pages[dimension.page_id]['dimensions'] += [{
                'dimension': dimension.title,
                'short_title': calculate_short_title(dimension.page.title, dimension.title),
                'guid': dimension.guid,
                'position': dimension.position
            }]

    # sort pages by order
    pages = sorted([pages[key] for key in pages],
                   key=lambda p: (p['topic'], p['subtopic_order'], p['measure_order']))

    # sort dimensions within pages by order
    for page in pages:
        page['dimensions'].sort(key=lambda dimension: dimension['position'])

    return render_template('dashboard/ethnicity_categorisation.html', ethnicity_categorisation=categorisation,
                           pages=pages)


@dashboard_blueprint.route('/ethnic-groups/<value_uri>')
@internal_user_required
@login_required
def ethnic_group(value_uri):
    ethnicity = categorisation_service.get_value_by_uri(value_uri)

    results = []
    page_count = 0
    value_title = ''
    if ethnicity:
        value_title = ethnicity.value
        dimension_links = EthnicGroupByDimension.query.filter_by(value=ethnicity.value).order_by(
            EthnicGroupByDimension.subtopic_guid, EthnicGroupByDimension.page_position,
            EthnicGroupByDimension.dimension_position, EthnicGroupByDimension.value_position).all()

        # Build a base tree of subtopics from the database
        subtopics = [{
            'guid': page.guid,
            'title': page.title,
            'uri': page.uri,
            'position': page.position,
            'topic_guid': page.parent_guid,
            'topic': page.parent.title,
            'topic_uri': page.parent.uri,
            'measures': []
        } for page in page_service.get_pages_by_type('subtopic')]
        subtopics = sorted(subtopics, key=lambda p: (p['topic_guid'], p['position']))

        # Build a list of dimensions
        dimension_list = [{
            'dimension_guid': d.dimension_guid,
            'dimension_title': d.dimension_title,
            'dimension_position': d.dimension_position,
            'page_guid': d.page_guid,
            'page_title': d.page_title,
            'page_uri': d.page_uri,
            'page_position': d.page_position,
            'page_version': d.page_version,
            'subtopic_guid': d.subtopic_guid
        } for d in dimension_links]

        # Integrate with the topic tree
        for subtopic in subtopics:
        # Build a datastructure of unique pages in the subtopic
            page_list = {d['page_guid']: {
                'guid': d['page_guid'],
                'title': d['page_title'],
                'uri': d['page_uri'],
                'position': d['page_position'],
                'url': url_for("static_site.measure_page",
                               topic=subtopic['topic_uri'],
                               subtopic=subtopic['uri'],
                               measure=d['page_uri'],
                               version=d['page_version'])
            } for d in dimension_list if d['subtopic_guid'] == subtopic['guid']}

            # Integrate the list of dimensions
            for page in page_list.values():
                page['dimensions'] = [{
                    'guid': d['dimension_guid'],
                    'title': d['dimension_title'],
                    'short_title': calculate_short_title(page['title'], d['dimension_title']),
                    'position': d['dimension_position']
                } for d in dimension_list if d['page_guid'] == page['guid']]

            subtopic['measures'] = sorted(page_list.values(), key=lambda p: p['position'])
            page_count += len(page_list)

        results = [s for s in subtopics if len(s['measures']) > 0]

    return render_template('dashboard/ethnic_group.html',
                           ethnic_group=value_title,
                           measure_count=page_count,
                           measure_tree=results)


def calculate_short_title(page_title, dimension_title):
    # Case 1 - try stripping the dimension title
    low_title = dimension_title.lower()
    if low_title.find(page_title.lower()) == 0:
        return dimension_title[len(page_title) + 1:]

    # Case 2 - try cutting using the last by
    by_pos = dimension_title.rfind('by')
    if by_pos >= 0:
        return dimension_title[by_pos:]

    # Case else - just return the original
    return dimension_title


def _in_range(week, begin, month, end=date.today()):
    if any([d for d in week if d.month > month]):
        return False
    return any([d for d in week if d >= begin]) and any([d for d in week if d <= end])


def _from_month_to_month(start, end):
    current = start
    while current < end:
        yield current
        current += timedelta(days=current.max.day)
    yield current


class EthnicGroupByDimension(db.Model):
    __tablename__ = 'ethnic_groups_by_dimension'

    subtopic_guid = db.Column('subtopic_guid', db.String())
    page_guid = db.Column('page_guid', db.String())
    page_title = db.Column('page_title', db.String())
    page_version = db.Column('page_version', db.String())
    page_status = db.Column('page_status', db.String())
    page_publication_date = db.Column('page_publication_date', db.Date())
    page_uri = db.Column('page_uri', db.String())
    page_position = db.Column('page_position', db.Integer())
    dimension_guid = db.Column('dimension_guid', db.String())
    dimension_title = db.Column('dimension_title', db.String())
    dimension_position = db.Column('dimension_position', db.Integer())
    categorisation = db.Column('categorisation', db.String())
    value = db.Column('value', db.String())
    value_position = db.Column('value_position', db.Integer())

    __table_args__ = (
        PrimaryKeyConstraint('dimension_guid', 'value', name='ethnic_groups_by_dimension_value_pk'),
        UniqueConstraint('dimension_guid', 'value', name='uix_ethnic_groups_by_dimension_value'),
        {})
