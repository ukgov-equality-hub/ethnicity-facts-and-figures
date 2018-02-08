import calendar
from datetime import date, datetime, timedelta

from flask import render_template
from flask_login import login_required
from sqlalchemy import not_, asc

from application.factory import page_service
from application.dashboard import dashboard_blueprint
from application.utils import internal_user_required

from application.cms.models import Page


# Temporary dashboard page until needs and usage properly worked out
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

    seven_days = timedelta(days=7)
    seven_days_ago = datetime.today() - seven_days
    in_last_week = Page.query.filter(
        Page.publication_date.isnot(None),
        Page.publication_date >= seven_days_ago
    ).all()

    first_publication = Page.query.filter(
        Page.publication_date.isnot(None)
    ).order_by(Page.publication_date.asc()).first()

    data = {'publications': len(original_publications),
            'major_updates': len(major_updates),
            'in_last_week': len(in_last_week),
            'first_publication': first_publication.publication_date}

    weeks = []

    for m in _from_month_to_month(first_publication.publication_date, date.today()):
        c = calendar.Calendar(calendar.MONDAY).monthdatescalendar(m.year, m.month)
        for week in c:
                if _in_range(week, first_publication.publication_date):
                    publications = Page.query.filter(
                        Page.publication_date.isnot(None),
                        Page.publication_date >= week[0],
                        Page.publication_date <= week[6],
                        Page.version == '1.0',
                        Page.page_type == 'measure'
                    ).order_by(asc(Page.publication_date)).all()
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

    weeks.reverse()
    data['weeks'] = weeks

    return render_template('dashboard/index.html', data=data)


@dashboard_blueprint.route('/measures')
@internal_user_required
@login_required
def measures():
    pages = page_service.get_pages_by_type('topic')
    return render_template('dashboard/measures.html', pages=pages)


def _in_range(week, begin, end=date.today()):
    return any([d for d in week if d >= begin]) and any([d for d in week if d <= end])


def _from_month_to_month(start, end):
    current = start
    while current < end:
        current += timedelta(days=current.max.day)
        yield current
