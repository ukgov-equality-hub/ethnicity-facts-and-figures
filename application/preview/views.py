from flask import render_template
from application.preview import preview_blueprint


# Note not making this login required for the moment?
@preview_blueprint.route('/page/<page_guid>')
def preview_page(page_guid):
    return render_template('preview/preview.html', page_guid=page_guid)
