from flask import (
    request,
    flash,
    url_for,
    redirect,
    render_template
)

from flask_login import (
    login_user,
    logout_user,
    login_required
)

from application.auth.forms import LoginForm
from application.auth.logins import get_user
from application.auth import auth_blueprint


@auth_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user(form.email.data)
        if user is not None:
            login_user(user)
            flash("Logged in successfully.")
            return redirect(request.args.get("next") or url_for("cms.index"))
        else:
            flash("Invalid login")
            form = LoginForm()
            render_template("auth/login.html", form=form)
    else:
        print("FAIL!")
    return render_template("auth/login.html", form=form)


@auth_blueprint.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
