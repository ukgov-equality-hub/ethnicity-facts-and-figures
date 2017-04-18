from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_login import login_required, login_user, logout_user
from flask.views import MethodView

from auth.user import User
from cms.forms.login import LoginForm

cms = Blueprint('cms', __name__)


class TestView(MethodView):
    decorators = [login_required]

    def get(self):
        return "Hello World"

cms.add_url_rule('/', view_func=TestView.as_view('live_data'))


# TODO: These views below could be class based
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