"""2018_04_11_add_population_topic

Revision ID: 2018_04_11_add_population_topic
Revises: 2018_06_27_chartbuilder_2
Create Date: 2018-04-11 14:17:50.447848

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.orm import sessionmaker

Session = sessionmaker()

# revision identifiers, used by Alembic.
revision = '2018_04_11_add_population_topic'
down_revision = '2018_06_27_chartbuilder_2'
branch_labels = None
depends_on = None

def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    # this feels awful? tests break if we don't do this because that database is empty and these
    # new records have a dependency on a homepage record via parent_guid.
    res = session.execute("select guid from page where guid='homepage';")
    results = res.fetchall()

    if results:
        op.execute('''
            INSERT INTO page (guid,
                            title,
                            uri,
                            page_type,
                            description,
                            additional_description,
                            version,
                            created_at,
                            parent_guid,
                            parent_version,
                            db_version_id)
                    VALUES (
                            'topic_population',
                            'British population',
                            'british-population',
                            'topic',
                            'Population statistics and Census data, also analysed by age, location and other factors',
                            'The government collects population data through the Census, which happens every 10 years, and other surveys.\n\nFind population statistics and demographic information for different ethnic groups in England and Wales. We have included data for Scotland where it’s available.',
                            '1.0',
                            now(),
                            'homepage',
                            '1.0',
                            1);''')


        op.execute('''
        INSERT INTO page (guid,
                            title,
                            uri,
                            page_type,
                            description,
                            version,
                            created_at,
                            db_version_id,
                            parent_guid,
                            parent_version,
                            position)
                    VALUES (
                            'subtopic_overall_population',
                            'Overall population',
                            'overall-population',
                            'subtopic',
                            'Overall population',
                            '1.0',
                            now(),
                            1,
                            'topic_population',
                            '1.0',
                            0);''')

    session.commit()

def downgrade():
    op.execute("DELETE from page WHERE guid = 'subtopic_overall_population';")
    op.execute("DELETE from page WHERE guid = 'topic_population';")