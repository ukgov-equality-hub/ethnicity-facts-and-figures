"""2018_04_11_add_sandbox_topic

Revision ID: 871aa70d5b6e
Revises: migrate_views
Create Date: 2018-04-11 14:17:50.447848

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

Session = sessionmaker()

# revision identifiers, used by Alembic.
revision = "2018_04_11_add_sandbox_topic"
down_revision = "migrate_views"
branch_labels = None
depends_on = None


def upgrade():

    bind = op.get_bind()
    session = Session(bind=bind)

    op.execute(
        """
        INSERT INTO page (guid,
                          title,
                          uri,
                          page_type,
                          description,
                          additional_description,
                          version,
                          created_at,
                          db_version_id)
                  VALUES (
                        'topic_testingspace',
                        'Testing space',
                        'testing-space',
                        'topic',
                        'Nothing in this section will ever be published on the website. You can use it as a practice area, or to create content that you want to use in documents or to share in other places. You can create, edit and delete measure pages, charts and tables. As we all share this space, please be considerate and do not edit or delete other people''s work unless you have their consent.',
                        'Nothing in this section will ever be published on the website. You can use it as a practice area, or to create content that you want to use in documents or to share in other places. You can create, edit and delete measure pages, charts and tables. As we all share this space, please be considerate and do not edit or delete other people''s work unless you have their consent.',
                        '1.0',
                        now(),
                        1);"""
    )

    op.execute(
        """
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
                        'subtopic_testmeasures',
                        'Test measures',
                        'test-measures',
                        'subtopic',
                        'Test measures',
                        '1.0',
                        now(),
                        1,
                        'topic_testingspace',
                        '1.0',
                        0);"""
    )

    op.execute(
        "UPDATE page SET parent_guid = 'topic_testingspace', parent_version = '1.0', position = 1 WHERE guid = 'subtopic_ethnicityintheuk';"
    )

    session.commit()


def downgrade():

    op.execute(
        "UPDATE page SET parent_guid = 'topic_cultureandcommunity', parent_version = '1.0', position = 10 WHERE guid = 'subtopic_ethnicityintheuk';"
    )

    op.execute("DELETE from page WHERE guid = 'subtopic_testmeasures';")

    op.execute("DELETE from page WHERE guid = 'topic_testingspace';")
