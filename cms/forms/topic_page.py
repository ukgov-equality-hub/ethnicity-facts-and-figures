from flask_wtf import Form
from wtforms import StringField
from wtforms import validators


class NewPageForm(Form):
    title = StringField('title', [validators.DataRequired()])

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        title = self.data['title']
        # TODO: Implement validation below
        # 1. Check page with this name does not exist
        # 2. Check this page name is not reserved (new & page_template should be reserved)
        if title:
            return True
        else:
            return False



