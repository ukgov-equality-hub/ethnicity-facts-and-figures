from flask_wtf import FlaskForm
from wtforms import StringField


class PageForm(FlaskForm):
    title = StringField('title')

    def validate(self):
        rv = FlaskForm.validate(self)
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



