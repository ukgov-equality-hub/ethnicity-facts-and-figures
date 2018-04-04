import calendar
from datetime import date, timedelta, datetime

from flask import render_template, jsonify, url_for
from flask_login import login_required
from sqlalchemy import not_
from sqlalchemy.orm import joinedload

from application.factory import page_service
from application.cms.categorisation_service import categorisation_service

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
def value_dashboard():
    print(datetime.now())
    latest_pages = Page.query.filter_by(latest=True)

    all_values = categorisation_service.get_all_categorisation_values()
    all_categorisations = categorisation_service.get_all_categorisations()

    val_cat_dict = {
        value_obj.value: {
            'value': value_obj.value,
            'pages': set([]),
            'dimensions': set([]),
            'categorisations': {
                cat.id: {'pages': set([]), 'dimensions': set([])} for cat in all_categorisations
            }
        } for value_obj in all_values}

    for page in latest_pages:
        for dimension in page.dimensions:
            for link in dimension.categorisation_links:
                # pass
                cat = link.categorisation
                if cat.family == 'Ethnicity':
                    for v in cat.values:
                        val_cat_dict[v.value]['pages'].add(page.guid)
                        val_cat_dict[v.value]['dimensions'].add(dimension.guid)
                        val_cat_dict[v.value]['categorisations'][cat.id]['pages'].add(page.guid)
                        val_cat_dict[v.value]['categorisations'][cat.id]['dimensions'].add(dimension.guid)

                    if link.includes_parents:
                        for v in cat.parent_values:
                            val_cat_dict[v.value]['pages'].add(page.guid)
                            val_cat_dict[v.value]['dimensions'].add(dimension.guid)
                            val_cat_dict[v.value]['categorisations'][cat.id]['pages'].add(page.guid)
                            val_cat_dict[v.value]['categorisations'][cat.id]['dimensions'].add(dimension.guid)
    results = {}
    for v in all_values:
        value_dict = {
            'page_total': len(val_cat_dict[v.value]['pages']),
            'dimension_total': len(val_cat_dict[v.value]['dimensions']),
            'categorisations': []
        }
        for categorisation_obj in all_categorisations:
            if len(val_cat_dict[v.value]['categorisations'][categorisation_obj.id]['dimensions']) > 0:
                page_count = len(val_cat_dict[v.value]['categorisations'][categorisation_obj.id]['pages'])
                dimension_count = len(val_cat_dict[v.value]['categorisations'][categorisation_obj.id]['dimensions'])
                value_dict['categorisations'] += [{
                    'categorisation': categorisation_obj.title,
                    'pages': page_count,
                    'dimensions': dimension_count
                }]
        results[v.value] = value_dict

    sorted_values = sorted(all_values, key=lambda v: v.position)
    ethnic_groups = [
        {
            'value': v.value,
            'position': v.position,
            'pages': results[v.value]['page_total'],
            'dimensions': results[v.value]['dimension_total'],
            'categorisations': results[v.value]['categorisations']
        }
        for v in sorted_values]

    return render_template('dashboard/ethnicity_values.html', ethnic_groups=ethnic_groups)


@dashboard_blueprint.route('/ethnicity-categorisations')
@internal_user_required
@login_required
def ethnicity_categorisations():
    categorisations = categorisation_service.get_all_categorisations_with_counts()
    return render_template('dashboard/ethnicity_categorisations.html', ethnicity_categorisations=categorisations)


@dashboard_blueprint.route('/ethnicity-categorisations/<categorisation_id>')
@internal_user_required
@login_required
def ethnicity_categorisation(categorisation_id):
    ethnicity_categorisation = categorisation_service.get_categorisation_by_id(categorisation_id)

    # get pages
    pages = {link.dimension.page_id:{
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
        'dimensions':[]
    } for link in ethnicity_categorisation.dimension_links if link.dimension.page.latest}

    # add dimensions to pages
    for dimension_link in ethnicity_categorisation.dimension_links:
        dimension = dimension_link.dimension
        if dimension.page.latest:
            short_title = dimension.title
            by_pos = dimension.title.rfind('by')
            if by_pos >= 0:
                short_title = short_title[by_pos:]

            pages[dimension.page_id]['dimensions'] += [{
                'dimension': dimension.title,
                'short_title': short_title,
                'guid': dimension.guid,
                'position': dimension.position
            }]

    # sort pages by order
    pages = sorted([pages[key] for key in pages], key = lambda page: (page['topic'], page['subtopic_order'], page['measure_order']))

    # sort dimensions within pages by order
    for page in pages:
        page['dimensions'].sort(key = lambda dimension: dimension['position'])

    return render_template('dashboard/ethnicity_categorisation.html', ethnicity_categorisation=ethnicity_categorisation, pages=pages)


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
