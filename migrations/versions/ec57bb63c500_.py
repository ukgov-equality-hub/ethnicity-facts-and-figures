"""empty message

Revision ID: ec57bb63c500
Revises: 8c3ea028a8c5
Create Date: 2017-06-30 13:06:24.686042

"""
import sqlalchemy as sa

from alembic import op
from application.cms.models import DbPage
from sqlalchemy.orm import Session


# revision identifiers, used by Alembic.

revision = 'ec57bb63c500'
down_revision = '8c3ea028a8c5'
branch_labels = None
depends_on = None



def upgrade():

    session = Session(bind=op.get_bind())

    for db_page in session.query(DbPage):
        for key, val in db_page.page_dict().items():
            if key not in ['dimensions']:
                setattr(db_page, key, val)
        session.add(db_page)
    session.commit()



def downgrade():
    pass
