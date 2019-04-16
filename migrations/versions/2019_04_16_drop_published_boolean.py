"""empty message

Revision ID: 2019_04_16_drop_published_boolean
Revises: 2019_04_05_not_null_orgs
Create Date: 2019-04-16 16:11:10.952637

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2019_04_16_drop_published_boolean"
down_revision = "2019_04_05_not_null_orgs"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("measure_version", "published")


def downgrade():
    op.add_column(
        "measure_version", sa.Column("published", sa.BOOLEAN(), autoincrement=False, nullable=False, default=False)
    )

    op.execute(
        """UPDATE measure_version
                  SET published = TRUE
                  WHERE published_at IS NOT NULL;
    """
    )
