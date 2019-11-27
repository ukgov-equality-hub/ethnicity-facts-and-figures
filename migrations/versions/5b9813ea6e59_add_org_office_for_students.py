"""add-org-office-for-students

Revision ID: 5b9813ea6e59
Revises: 62308cd181b2
Create Date: 2019-11-27 10:55:56.488344

"""
from alembic import op
from sqlalchemy.orm import sessionmaker

from application.cms.models import Organisation, TypeOfOrganisation

Session = sessionmaker()

# revision identifiers, used by Alembic.
revision = "5b9813ea6e59"
down_revision = "62308cd181b2"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    ofs_org = Organisation(
        id="PB1253",
        name="Office for Students",
        other_names="{}",
        abbreviations="{OfS}",
        organisation_type=TypeOfOrganisation.EXECUTIVE_NON_DEPARTMENTAL_PUBLIC_BODY,
    )

    session.add(ofs_org)


def downgrade():
    op.get_bind()
    op.execute(
        """
        DELETE FROM organisation WHERE id = 'PB1253'
        """
    )
