from flask import render_template, current_app, abort, url_for
from flask_login import login_required
from itsdangerous import SignatureExpired, BadTimeSignature, BadSignature
from sqlalchemy.orm.exc import NoResultFound

from application.cms.models import MeasureVersion
from application.review import review_blueprint
from application.utils import decode_review_token, generate_review_token
from application import db


@review_blueprint.route("/<review_token>")
def review_page(review_token):
    try:
        id, version = decode_review_token(review_token, current_app.config)
        measure_version = MeasureVersion.query.filter_by(guid=id, version=version, review_token=review_token).one()

        if measure_version.status not in ["DEPARTMENT_REVIEW", "APPROVED"]:
            return render_template("static_site/not_ready_for_review.html", preview=True)

        dimensions = [dimension.to_dict() for dimension in measure_version.dimensions]

        return render_template(
            "static_site/measure.html",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_version=measure_version,
            dimensions=dimensions,
            preview=True,
        )

    except SignatureExpired as e:
        current_app.logger.exception(e)
        return render_template("review/token_expired.html")

    except (BadSignature, BadTimeSignature, NoResultFound) as e:
        current_app.logger.exception(e)
        abort(404)


@review_blueprint.route("/new-review-url/<id>/<version>")
@login_required
def get_new_review_url(id, version):
    try:
        token = generate_review_token(id, version)
        measure_version = MeasureVersion.query.filter_by(guid=id, version=version).one()
        measure_version.review_token = token
        db.session.commit()
        url = url_for("review.review_page", review_token=measure_version.review_token, _external=True)
        expires = measure_version.review_token_expires_in(current_app.config)
        day = "day" if expires == 1 else "days"
        return """<a href="{url}">Review link</a> expires in {expires} {day}
                    <button id="copy-to-clipboard" class="button neutral">Copy link</button>
                    <input id="review-link" value="{url}">
                    """.format(
            expires=expires, day=day, url=url
        )

    except Exception as e:
        current_app.logger.exception(e)
        abort(500)
