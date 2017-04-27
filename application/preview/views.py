from flask import (
    render_template,
    abort
)

from application.preview import preview_blueprint
from application.cms.page_service import page_service


# Note not making this login required for the moment?
@preview_blueprint.route('/page/<slug>')
def preview_page(slug):
    page = page_service.get_page(slug)
    return render_template('preview/preview.html', slug=slug, page=page)
