from flask import (
    render_template
)

from flask_login import login_required

from application.preview import preview_blueprint
from application.cms.page_service import page_service


@preview_blueprint.route('/page/<slug>')
@login_required
def preview_page(slug):
    page = page_service.get_page(slug)
    return render_template('preview/preview.html', slug=slug, page=page)
