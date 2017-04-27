
from flask import (
    redirect,
    render_template,
    request,
    url_for,
    abort
)

from flask_login import login_required

from application.cms import cms_blueprint
from application.cms.exceptions import PageNotFoundException
from application.cms.forms import PageForm
from application.cms.models import publish_status
from application.cms.page_service import page_service


@cms_blueprint.route('/')
@login_required
def index():
    pages = page_service.get_pages()
    return render_template('cms/index.html', pages=pages)


@cms_blueprint.route('/page', methods=['GET', 'POST'])
@login_required
def create_page():
    pages = page_service.get_pages()
    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.form)
        if form.validate():
            page = page_service.create_page(data=form.data)
            pages = page_service.get_pages()
            return redirect(url_for("cms.edit_page", slug=page.meta.uri, pages=pages))
    return render_template("cms/new_page.html", form=form, pages=pages)


@cms_blueprint.route('/page/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_page(slug):
    try:
        page = page_service.get_page(slug)
    except PageNotFoundException:
        abort(404)

    form = PageForm(obj=page)
    if request.method == 'POST':
        form = PageForm(request.form)
        if form.validate():
            page_service.update_page(page, data=form.data)

    current_status = page.meta.status
    available_actions = page.available_actions()
    if 'APPROVE' in available_actions:
        numerical_status = page.publish_status(numerical=True)
        approval_state = publish_status.inv[numerical_status+1]

    pages = page_service.get_pages()

    context = {
        'form': form,
        'slug': slug,
        'status': current_status,
        'available_actions': available_actions,
        'next_approval_state': approval_state if 'APPROVE' in available_actions else None,
        'pages': pages
    }

    return render_template("cms/edit_page.html", **context)


@cms_blueprint.route('/pages/<slug>/publish')
@login_required
def publish_page(slug):
    page = page_service.next_state(slug)
    return redirect(url_for("cms.edit_page", slug=page.meta.uri))


@cms_blueprint.route('/pages/<slug>/reject')
@login_required
def reject_page(slug):
    page = page_service.reject_page(slug)
    return redirect(url_for("cms.edit_page",  slug=page.meta.uri))
