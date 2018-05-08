import calendar
from datetime import date, timedelta

from flask import render_template, url_for, jsonify
from flask_login import login_required
from slugify import slugify

from application.dashboard.models import EthnicGroupByDimension, CategorisationByDimension, PageByLowestLevelOfGeography
from sqlalchemy import not_

from application.dashboard.trello_service import trello_service
from application.factory import page_service

from application.dashboard import dashboard_blueprint
from application.cms.categorisation_service import categorisation_service
from application.utils import internal_user_required

from application.cms.models import Page, LowestLevelOfGeography


def page_in_week(page, week):
    return page.publication_date >= week[0] and page.publication_date <= week[6]


@dashboard_blueprint.route('/')
@internal_user_required
@login_required
def index():
    return render_template('dashboards/index.html')


@dashboard_blueprint.route('/published')
@internal_user_required
@login_required
def published():
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

    return render_template('dashboards/publications.html', data=data)


@dashboard_blueprint.route('/measures')
@internal_user_required
@login_required
def measures_list():
    pages = page_service.get_pages_by_type('topic')
    return render_template('dashboards/measures.html', pages=pages)


@dashboard_blueprint.route('/measure-progress')
@internal_user_required
@login_required
def measure_progress():
    if trello_service.is_initialised():
        measure_cards = trello_service.get_measure_cards()
        planned_count = len([measure for measure in measure_cards if measure['stage'] == 'planned'])
        progress_count = len([measure for measure in measure_cards if measure['stage'] == 'progress'])
        review_count = len([measure for measure in measure_cards if measure['stage'] == 'review'])
        published_count = len([measure for measure in measure_cards if measure['stage'] == 'published'])

        return render_template('dashboards/measure_progress.html', measures=measure_cards, planned_count=planned_count,
                               progress_count=progress_count, review_count=review_count,
                               published_count=published_count)
    else:
        return render_template('dashboards/measure_progress.html', measures=[], planned_count=0,
                               progress_count=0, review_count=0, published_count=0)


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
                                       'url': url_for("dashboards.ethnic_group", value_uri=slugify(link.value)),
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

    return render_template('dashboards/ethnicity_values.html', ethnic_groups=sorted_ethnicity_list)


@dashboard_blueprint.route('/ethnicity-categorisations')
@internal_user_required
@login_required
def ethnicity_categorisations():
    dimension_links = CategorisationByDimension.query.all()

    categorisation_rows = categorisation_service.get_all_categorisations()
    categorisations = {
        categorisation.id: {
            "id": categorisation.id,
            "title": categorisation.title,
            "position": categorisation.position,
            "has_parents": len(categorisation.parent_values) > 0,
            "pages": set([]),
            "dimension_count": 0,
            "includes_parents_count": 0,
            "includes_all_count": 0,
            "includes_unknown_count": 0
        }
        for categorisation in categorisation_rows
    }
    for link in dimension_links:
        categorisations[link.categorisation_id]['pages'].add(link.page_guid)
        categorisations[link.categorisation_id]['dimension_count'] += 1
        if link.includes_parents:
            categorisations[link.categorisation_id]['includes_parents_count'] += 1
        if link.includes_all:
            categorisations[link.categorisation_id]['includes_all_count'] += 1
        if link.includes_unknown:
            categorisations[link.categorisation_id]['includes_unknown_count'] += 1

    categorisations = list(categorisations.values())
    categorisations = [c for c in categorisations if c['dimension_count'] > 0]
    categorisations.sort(key=lambda x: x['position'])

    for categorisation in categorisations:
        categorisation['measure_count'] = len(categorisation['pages'])

    return render_template('dashboards/ethnicity_categorisations.html',
                           ethnicity_categorisations=categorisations)


@dashboard_blueprint.route('/ethnicity-categorisations/<categorisation_id>')
@internal_user_required
@login_required
def ethnicity_categorisation(categorisation_id):
    categorisation = categorisation_service.get_categorisation_by_id(categorisation_id)

    page_count = 0
    results = []
    categorisation_title = ''

    if categorisation:
        categorisation_title = categorisation.title
        dimension_links = CategorisationByDimension.query.filter_by(categorisation_id=categorisation_id).order_by(
            CategorisationByDimension.subtopic_guid, CategorisationByDimension.page_position,
            CategorisationByDimension.dimension_position).all()

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
            # Build a data structure of unique pages in the subtopic
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

    return render_template('dashboards/ethnicity_categorisation.html',
                           categorisation_title=categorisation_title,
                           page_count=page_count,
                           measure_tree=results)


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
            # Build a data structure of unique pages in the subtopic
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

    return render_template('dashboards/ethnic_group.html',
                           ethnic_group=value_title,
                           measure_count=page_count,
                           measure_tree=results)


@dashboard_blueprint.route('/geographic-breakdown')
@internal_user_required
@login_required
def locations():
    # build framework
    location_dict = {location.name: {
        'location': location,
        'pages': []
    } for location in LowestLevelOfGeography.query.all()}

    # integrate with page geography
    page_geogs = PageByLowestLevelOfGeography.query.all()
    for page_geog in page_geogs:
        location_dict[page_geog.geography_name]['pages'] += [page_geog.page_guid]

    # convert to list and sort
    location_list = list(location_dict.values())
    location_list.sort(key=lambda x: x['location'].position)

    location_levels = [{
        "name": item['location'].name,
        "url": url_for('dashboards.location', slug=slugify(item['location'].name)),
        "pages": len(item['pages'])
    } for item in location_list if len(item['pages']) > 0]

    return render_template('dashboards/geographic-breakdown.html',
                           location_levels=location_levels)


@dashboard_blueprint.route('/geographic-breakdown/<slug>')
@internal_user_required
@login_required
def location(slug):
    # get the
    loc = _deslugifiedLocation(slug)

    # get the measures that implement this as PageByLowestLevelOfGeography objects
    measures = PageByLowestLevelOfGeography.query.filter(
        PageByLowestLevelOfGeography.geography_name == loc.name).order_by(
        PageByLowestLevelOfGeography.page_position).all()

    # Build a base tree of subtopics from the database
    subtopics = [{
        'guid': page.guid,
        'title': page.title,
        'uri': page.uri,
        'position': page.position,
        'topic_guid': page.parent_guid,
        'topic': page.parent.title,
        'topic_uri': page.parent.uri,
        'measures': [{
            'title': measure.page_title,
            'url': url_for("static_site.measure_page",
                           topic=page.parent.uri,
                           subtopic=page.uri,
                           measure=measure.page_uri,
                           version=measure.page_version)
        } for measure in measures if measure.subtopic_guid == page.guid]
    } for page in page_service.get_pages_by_type('subtopic')]

    # dispose of subtopics without content
    subtopics = [s for s in subtopics if len(s['measures']) > 0]

    # sort
    subtopics.sort(key=lambda p: (p['topic_guid'], p['position']))

    page_count = 0
    for subtopic in subtopics:
        page_count += len(subtopic['measures'])

    return render_template('dashboards/lowest-level-of-geography.html',
                           level_of_geography=loc.name,
                           page_count=page_count,
                           measure_tree=subtopics)


def _deslugifiedLocation(slug):
    for location in LowestLevelOfGeography.query.all():
        if slugify(location.name) == slug:
            return location
    return None


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
