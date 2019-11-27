"""add-org-office-for-students

Revision ID: 5b9813ea6e59
Revises: 62308cd181b2
Create Date: 2019-11-27 10:55:56.488344

"""
from alembic import op

from application.cms.models import Organisation


# revision identifiers, used by Alembic.
revision = "5b9813ea6e59"
down_revision = "62308cd181b2"
branch_labels = None
depends_on = None


def upgrade():
    if Organisation.query.filter_by(id="PB1253").count() == 0:
        op.execute(
            """
            INSERT INTO organisation
                (id, name, other_names, abbreviations, organisation_type)
            VALUES
                ('PB1253', 'Office for Students', '{}', '{OfS}', 'EXECUTIVE_NON_DEPARTMENTAL_PUBLIC_BODY')
        """
        )  # noqa


def downgrade():
    op.execute(
        """
        DELETE FROM organisation WHERE id = 'PB1253'
    """
    )
