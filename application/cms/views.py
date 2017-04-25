import os
from flask import (
    redirect,
    render_template,
    request,
    url_for,
    current_app
)

from flask_login import login_required

from application.cms import cms_blueprint
from application.cms.forms import PageForm
from application.cms.models import Page, Struct, publish_status


@cms_blueprint.route('/')
@login_required
def index():
    pages = _get_pages(current_app.config)
    return render_template('cms/index.html', pages=pages)


@cms_blueprint.route('/pages/new', methods=['GET', 'POST'])
@login_required
def create_page():
    pages = _get_pages(current_app.config)
    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.form)
        if form.validate():
            title = form.data['title']
            page = Page(guid=title, config=current_app.config)
            page.create_new_page(initial_data=form.data)

            # TODO: redirect to edit page
            # return redirect("/pages/" + id)
            return redirect(url_for("cms.edit_page", guid=title, pages=pages))
    return render_template("cms/new_page.html", form=form, pages=pages)


@cms_blueprint.route('/pages/<guid>/edit', methods=['GET', 'POST'])
@login_required
def edit_page(guid):
    # TODO: Currently this page is view only
    # TODO: 404 when page not found
    page = Page(guid=guid, config=current_app.config)
    page_content = page.file_content('page.json')
    page_data = Struct(**page_content)
    form = PageForm(obj=page_data)
    if request.method == 'POST':
        form = PageForm(request.form)
        if form.validate():
            page.update_page_data(new_data=form.data)

    current_status = page.publish_status()
    available_actions = page.available_actions()
    if 'APPROVE' in available_actions:
        # Progress button available, determine text
        numerical_status = page.publish_status(numerical=True)
        approval_state = publish_status.inv[numerical_status+1]

    pages = _get_pages(current_app.config)


    context = {
        'form': form,
        'guid': guid,
        'status': current_status,
        'available_actions': available_actions,
        'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
        'pages': pages
    }

    return render_template("cms/edit_page.html", **context)


@cms_blueprint.route('/pages/<guid>/publish')
@login_required
def publish_page(guid):
    page = Page(guid=guid, config=current_app.config)
    page.publish()
    pages = _get_pages(current_app.config)
    return redirect(url_for("cms.edit_page", guid=guid, pages=pages))


@cms_blueprint.route('/pages/<guid>/reject')
@login_required
def reject_page(guid):
    page = Page(guid=guid, config=current_app.config)
    page.reject()
    pages = _get_pages(current_app.config)
    return redirect(url_for("cms.edit_page", guid=guid, pages=pages))


# temp hack to get all pages
def _get_pages(config):
    page_dir = '{}/{}'.format(config['REPO_DIR'], config['CONTENT_DIR'])
    pages = [Page(page, config) for page in os.listdir(page_dir) if page.startswith('topic_')]
    page_dict = [{'guid': page.guid, 'content': page.file_content('page.json')} for page in pages]
    return page_dict
