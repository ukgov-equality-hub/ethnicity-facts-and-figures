"""empty message

Revision ID: e553b195fe90
Revises: 2c6aab556fef
Create Date: 2017-07-14 10:46:24.359860

"""
import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from application.cms.models import DbDimension

# revision identifiers, used by Alembic.
revision = 'e553b195fe90'
down_revision = '2c6aab556fef'
branch_labels = None
depends_on = None


def upgrade():

    session = Session(bind=op.get_bind())

    for d in session.query(DbDimension):

        modified = False

        if d.chart is not None and isinstance(d.chart, str):
            if d.chart.strip() == '':
                d.chart = sa.null()
            else:
                d.chart = json.loads(d.chart)
            modified = True

        if d.chart_source_data is not None and isinstance(d.chart_source_data, str):
            if d.chart_source_data.strip() == '':
                d.chart_source_data = sa.null()
            else:
                d.chart_source_data = json.loads(d.chart_source_data)
            modified = True

        if d.table is not None and isinstance(d.table, str):
            if d.table.strip() == '':
                d.table = sa.null()
            else:
                d.table = json.loads(d.table)
            modified = True

        if d.table_source_data is not None and isinstance(d.table_source_data, str):
            if d.table_source_data.strip() == '':
                d.table_source_data = sa.null()
            else:
                d.table_source_data = json.loads(d.table_source_data)
            modified = True

        if modified:
            session.add(d)
            session.commit()

    for d in session.query(DbDimension):

        chart_modified = False
        table_modified = False

        if d.chart_source_data is not None:
            if d.chart_source_data.get('chartOptions') is not None:
                for key, val in d.chart_source_data.get('chartOptions').items():
                    if val is None:
                        d.chart_source_data['chartOptions'][key] = '[None]'
                        chart_modified = True

        if d.table_source_data is not None:
            if d.table_source_data.get('tableOptions') is not None:
                for key, val in d.table_source_data.get('tableOptions').items():
                    if val is None:
                        d.table_source_data['tableOptions'][key] = '[None]'
                        table_modified = True

        if chart_modified:
            flag_modified(d, 'chart_source_data')

        if table_modified:
            flag_modified(d, 'table_source_data')

        session.add(d)
        session.commit()


def downgrade():
    pass