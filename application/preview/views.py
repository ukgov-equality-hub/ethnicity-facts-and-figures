from flask import (
    render_template,
    current_app,
    abort
)

from application.preview import preview_blueprint
from application.cms.models import Page


# Note not making this login required for the moment?
@preview_blueprint.route('/page/<guid>')
def preview_page(guid):
    page = Page(guid=guid, config=current_app.config)
    try:
        page_content = page.file_content('page.json')
        return render_template('preview/preview.html', guid=guid, page_content=page_content)
    except FileNotFoundError:
        abort(404)
