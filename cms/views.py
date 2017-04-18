from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_login import login_required, login_user, logout_user
from flask.views import MethodView

from cms.forms.login import LoginForm
from cms.forms.topic_page import NewPageForm
from page.utils import create_page, save_page

cms = Blueprint('cms', __name__)


class TestView(MethodView):
    decorators = [login_required]

    def get(self):
        return render_template("index.html",)

cms.add_url_rule('/', view_func=TestView.as_view('live_data'))


class CreatePage(MethodView):
    decorators = [login_required]

    def get(self):
        return render_template("new_page.html",)

    def post(self):
        form = NewPageForm(request.form)
        if form.validate():
            # TODO: access page name
            create_page('topic_page', "topic")
            save_page('topic_page', form.data)
            # TODO: redirect to edit page
            # return redirect("/pages/" + id)
        return render_template("new_page.html",)

cms.add_url_rule('/pages/new', view_func=CreatePage.as_view('create_page'))


class EditPage(MethodView):
    def get(self):
        pass

    def post(self):
        pass

#cms.add_url_rule('/pages/new', view_func=EditPage.as_view('edit_page'))


# TODO: These views below could be class based, above they could be non class based
@cms.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # login and validate the user...
        login_user(form.user)
        flash("Logged in successfully.")
        return redirect(request.args.get("next") or url_for("cms.live_data"))
    else:
        print("FAIL!")
    return render_template("login.html", form=form)


@cms.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("cms.login"))