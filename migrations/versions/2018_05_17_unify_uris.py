"""Update old version URIs to be the same as the latest version

Revision ID: 2018_05_17_unify_uris
Revises: 2018_05_04_coalesce_contacts
Create Date: 2018-05-17 11:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2018_05_17_unify_uris"
down_revision = "2018_05_04_coalesce_contacts"
branch_labels = None
depends_on = None


def upgrade():

    # Find pages where old versions have a different URI from the latest version and update old URIs to match the new
    op.get_bind()
    op.execute(
        """
        UPDATE page
        SET uri = subquery.uri
        FROM (SELECT guid, uri
              FROM page
              WHERE external_edit_summary = 'Technical change: Updated url to match page title.'
        ) AS subquery
        WHERE page.guid = subquery.guid
        AND page.uri != subquery.uri;
    """
    )


def downgrade():
    # No way to undo this!
    pass
