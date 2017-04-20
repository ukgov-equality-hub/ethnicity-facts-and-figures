from flask import redirect
from flask import render_template, request
from flask import url_for
from flask_login import login_required
from application.cms import cms_blueprint
from application.cms.forms import PageForm
from application.cms.models import Page, Struct


@cms_blueprint.route('/')
@login_required
def index():
    return render_template('cms/index.html')


@cms_blueprint.route('/pages/new', methods=['GET', 'POST'])
@login_required
def create_page():
    form = PageForm()
    if request.method == 'POST':
        form = PageForm(request.form)
        if form.validate():
            # TODO: access page name
            title = form.data['title']
            page = Page(guid=title)
            page.create_new_page(initial_data=form.data)
            # TODO: redirect to edit page
            # return redirect("/pages/" + id)
            return redirect(url_for("cms.edit_page"))
    return render_template("cms/new_page.html", form=form)


@cms_blueprint.route('/pages/<guid>/edit', methods=['GET', 'POST'])
@login_required
def edit_page(guid):
    # TODO: Currently this page is view only
    page = Page(guid=guid)
    page_content = page.page_content()
    page_data = Struct(**page_content)
    form = PageForm(obj=page_data)

    return render_template("cms/edit_page.html", form=form)


@cms_blueprint.route('/pages/<guid>/publish')
@login_required
def publish_page(guid):
    page = Page(guid=guid)
    page.publish()
    return redirect(url_for("cms.edit_page", guid=guid))


@cms_blueprint.route('/pages/<guid>/reject')
@login_required
def reject_page(guid):
    page = Page(guid=guid)
    page.reject()
    return redirect(url_for("cms.edit_page", guid=guid))
