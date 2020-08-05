from flask import render_template, current_app, abort, url_for
from flask_login import login_required, current_user
from itsdangerous import SignatureExpired, BadTimeSignature, BadSignature
from sqlalchemy.orm.exc import NoResultFound

from application import db
from application.cms.models import MeasureVersion
from application.review import review_blueprint
from application.utils import decode_review_token, generate_review_token


@review_blueprint.route("/<review_token>")
def review_page(review_token):
    try:
        # TODO: Once all guid-based tokens have expired adjust this to only filter by ID & token.
        id, version = decode_review_token(review_token, current_app.config)
        if version is None:
            # New-style token with id only
            measure_version = MeasureVersion.query.filter_by(id=id, review_token=review_token).one()
        else:
            # Old-style token with guid + version
            measure_version = MeasureVersion.query.filter_by(guid=id, version=version, review_token=review_token).one()
        # TODO End

        if measure_version.status not in ["DEPARTMENT_REVIEW", "APPROVED"]:
            return render_template("static_site/not_ready_for_review.html", preview=True)

        # define template
        template = "static_site/measure.html"

        if measure_version.template_version != "1":
            template = f"static_site/measure_v{measure_version.template_version}.html"

        return render_template(
            template,
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_version=measure_version,
            preview=True,
            latest_url=False,
        )

    except SignatureExpired as e:
        current_app.logger.exception(e)
        return render_template("review/token_expired.html")

    except (BadSignature, BadTimeSignature, NoResultFound) as e:
        current_app.logger.exception(e)
        abort(404)


# TODO: This is super-weird the way it sends a fragment of HTML back to the page to swap in. There must be a better way.
# TODO: This should probably be a POST action as it changes state on the server
@review_blueprint.route("/new-review-url/<id>")
@login_required
def get_new_review_url(id):
    measure_version = MeasureVersion.query.filter_by(id=id).one()
    if not current_user.can_access_measure(measure_version.measure):
        abort(403)

    token = generate_review_token(id)
    measure_version.review_token = token
    db.session.commit()
    url = url_for("review.review_page", review_token=measure_version.review_token, _external=True)
    expires = measure_version.review_token_expires_in(current_app.config)
    day = "day" if expires == 1 else "days"
    return """<a href="{url}">Review link</a> expires in {expires} {day}
                <button id="copy-to-clipboard" class="govuk-button eff-button--secondary-quiet">Copy link</button>
                <input id="review-link" value="{url}">
                """.format(
        expires=expires, day=day, url=url
    )
