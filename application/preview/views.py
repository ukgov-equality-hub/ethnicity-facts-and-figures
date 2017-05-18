from flask import (
    render_template
)

from flask_login import login_required

from application.preview import preview_blueprint
from application.cms.page_service import page_service


@preview_blueprint.route('/<topic>')
@login_required
def preview_page(topic):
    page = page_service.get_page(topic)
    # for the moment use the preview template but when topic
    # page is ready in static site, use that instead
    return render_template('preview/preview.html', topic=topic, page=page)


@preview_blueprint.route('/<topic>/<subtopic>/<measure>')
@login_required
def preview_measure(topic, subtopic, measure):
    measure_page = page_service.get_page(measure)
    subtopic_page = page_service.get_page(subtopic)
    return render_template('measure.html', parent=subtopic_page, measure_page=measure_page)
