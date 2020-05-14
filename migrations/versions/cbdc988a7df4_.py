"""empty message

Revision ID: cbdc988a7df4
Revises: 6fa486580023
Create Date: 2018-02-09 12:08:16.417127

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "cbdc988a7df4"
down_revision = "6fa486580023"
branch_labels = None
depends_on = None


def upgrade():
    op.get_bind()
    op.execute(
        """
      INSERT INTO type_of_statistic (id, internal, external, position)
      VALUES (4, 'Non-official statistics (not produced by a Government department or agency)', 'Non-official statistics', 4);
    """
    )

    op.execute(
        """
      UPDATE page SET type_of_statistic_id = 2 WHERE guid IN ('BEIS 010', 'BEIS 011', 'DCLG 019', 'DWP 015');
      UPDATE page SET type_of_statistic_id = 3 WHERE guid = 'DWP 008';
      UPDATE page SET type_of_statistic_id = 4 WHERE guid = 'BEIS 004';
    """
    )


def downgrade():
    pass
