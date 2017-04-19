from flask import render_template, request
from flask_login import login_required
from application.cms import cms_blueprint
from application.cms.forms import PageForm
from application.cms.models import Page


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
    return render_template("cms/new_page.html", form=form)


# @cms_blueprint.route('/pages/<guid>/edit', methods=['GET', 'POST'])
# @login_required
# def edit_page():
#     page_data = load_page(guid)
#     # Struct(**data)
#     form = PageForm(obj=page_data)
#
#     return render_template("cms/edit_page.html", form=form)
#
# @cms_blueprint.route('/pages/<guid>/publish', methods=['GET', 'POST'])
# @login_required
# def edit_page():
#     page_data = load_page(guid)
#     # Struct(**data)
#     form = PageForm(obj=page_data)
#
#     return render_template("cms/edit_page.html", form=form)

