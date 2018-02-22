import calendar
from datetime import date, timedelta

from flask import render_template
from flask_login import login_required
from sqlalchemy import not_

from application.factory import page_service
from application.dashboard import dashboard_blueprint
from application.cms.categorisation_service import categorisation_service
from application.utils import internal_user_required

from application.cms.models import Page


@dashboard_blueprint.route('/')
@internal_user_required
@login_required
def index():

    original_publications = Page.query.filter(
        Page.publication_date.isnot(None),
        Page.version == '1.0',
        Page.page_type == 'measure'
    ).all()

    major_updates = Page.query.filter(
        Page.publication_date.isnot(None),
        Page.page_type == 'measure',
        not_(Page.version.startswith('1'))
    ).all()

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
                    publications = Page.query.filter(
                        Page.publication_date.isnot(None),
                        Page.publication_date >= week[0],
                        Page.publication_date <= week[6],
                        Page.version == '1.0',
                        Page.page_type == 'measure'
                    ).order_by(Page.publication_date.desc()).all()
                    major_updates = Page.query.filter(
                        Page.publication_date.isnot(None),
                        Page.publication_date >= week[0],
                        Page.publication_date <= week[6],
                        not_(Page.version.startswith('1')),
                        Page.page_type == 'measure'
                    ).all()

                    weeks.append({'week': week[0],
                                  'publications': publications,
                                  'major_updates': major_updates})

                    if not cumulative_total:
                        cumulative_total.append(len(publications) + len(major_updates))
                    else:
                        last_total = cumulative_total[-1]
                        cumulative_total.append(last_total + len(publications) + len(major_updates))
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


@dashboard_blueprint.route('/ethnicity_categorisations')
@internal_user_required
@login_required
def ethnicity_categorisations():
    ethnicity_categorisations = categorisation_service.get_all_categorisations_with_counts()
    return render_template('dashboard/ethnicity_categorisations.html', ethnicity_categorisations = ethnicity_categorisations)


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
