from flask import Blueprint

review_blueprint = Blueprint('review', __name__, url_prefix='/review')

from application.review.views import review_page  # noqa
