from flask import Blueprint
from flask.views import MethodView

cms = Blueprint('cms', __name__)

class Test(MethodView):
    def get(self):
        return "Hello World"

cms.add_url_rule('/', view_func=Test.as_view('live_data'))