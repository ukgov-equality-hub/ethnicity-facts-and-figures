"""
Update measure version

Revision ID: 2020_07_06_add_template_version
Revises: 2020_06_22_manage_topics
Create Date: 2020-05-19 14:02:04.242855

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2020_07_06_add_template_version"
down_revision = "2020_06_22_manage_topics"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("measure_version", sa.Column("template_version", sa.String(length=2), nullable=True))

    op.get_bind()
    op.execute(
        """
            UPDATE measure_version SET template_version = '1';
        """
    )
    op.alter_column("measure_version", "template_version", nullable=False)


def downgrade():
    op.drop_column("measure_version", "template_version")
