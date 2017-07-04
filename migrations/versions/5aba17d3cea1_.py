"""empty message

Revision ID: 5aba17d3cea1
Revises: 1a9cee041761
Create Date: 2017-07-04 10:22:01.717087

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from application.cms.models import DbDimension
from sqlalchemy.orm.attributes import flag_modified

# revision identifiers, used by Alembic.
revision = '5aba17d3cea1'
down_revision = '1a9cee041761'
branch_labels = None
depends_on = None


def upgrade():

    session = Session(bind=op.get_bind())

    for d in session.query(DbDimension):
        if d.chart_source_data is not None and isinstance(d.chart_source_data, dict):
            if d.chart_source_data.get('chartOptions') and isinstance(d.chart_source_data.get('chartOptions'), dict):
                modified = False
                for key, val in d.chart_source_data.get('chartOptions').items():
                    if val is None:
                        d.chart_source_data['chartOptions'][key] = '[None]'
                        modified = True

                if modified:
                    flag_modified(d, 'chart_source_data')
                    session.add(d)
                    session.commit()

def downgrade():
    pass
