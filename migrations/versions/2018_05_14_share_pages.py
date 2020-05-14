"""Update to user types and capabilities to allow sharing of pages with departmental users

 * Adds new user_types Enum
 * Adds user_type column to users table and populates it with values from user_types Enum based on current capabilities
 * Updates capabilities column with new lists of allowed actions as defined in auth.models.CAPABILITIES
 * Adds new user_page table to record which (departmental) users have access to which pages

Revision ID: 2018_05_14_share_pages
Revises: 2018_05_17_unify_uris
Create Date: 2018-05-14 11:49:34.203665

"""
from alembic import op
import sqlalchemy as sa

from application.auth.models import TypeOfUser, CAPABILITIES

# revision identifiers, used by Alembic.
revision = "2018_05_14_share_pages"
down_revision = "2018_05_17_unify_uris"
branch_labels = None
depends_on = None


def upgrade():

    type_of_user_types = sa.Enum("RDU_USER", "DEPT_USER", "ADMIN_USER", "DEV_USER", name="type_of_user_types")

    type_of_user_types.create(op.get_bind())

    op.add_column("users", sa.Column("user_type", type_of_user_types, nullable=True))

    op.execute(
        """
        UPDATE users SET user_type = '%s' WHERE 'INTERNAL_USER' = any(capabilities);
        UPDATE users SET user_type = '%s' WHERE 'DEPARTMENTAL_USER' = any(capabilities);
        UPDATE users SET user_type = '%s' WHERE 'ADMIN' = any(capabilities);
        UPDATE users SET user_type = '%s' WHERE 'DEVELOPER' = any(capabilities);
    """
        % (TypeOfUser.RDU_USER.name, TypeOfUser.DEPT_USER.name, TypeOfUser.ADMIN_USER.name, TypeOfUser.DEV_USER.name)
    )

    op.execute(
        """
        UPDATE users SET capabilities = '{%s}' WHERE user_type = '%s'
    """
        % (",".join(CAPABILITIES[TypeOfUser.RDU_USER]), TypeOfUser.RDU_USER.name)
    )

    op.execute(
        """
            UPDATE users SET capabilities = '{%s}' WHERE user_type = '%s'
        """
        % (",".join(CAPABILITIES[TypeOfUser.DEPT_USER]), TypeOfUser.DEPT_USER.name)
    )

    op.execute(
        """
              UPDATE users SET capabilities = '{%s}' WHERE user_type = '%s'
          """
        % (",".join(CAPABILITIES[TypeOfUser.ADMIN_USER]), TypeOfUser.ADMIN_USER.name)
    )

    op.execute(
        """
              UPDATE users SET capabilities = '{%s}' WHERE user_type = '%s'
          """
        % (",".join(CAPABILITIES[TypeOfUser.DEV_USER]), TypeOfUser.DEV_USER.name)
    )

    op.create_table(
        "user_page",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("page_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"],),
        sa.PrimaryKeyConstraint("user_id", "page_id"),
    )


def downgrade():

    op.execute(
        """
        UPDATE users
        SET capabilities = '{INTERNAL_USER}'
        WHERE capabilities = '{%s}'
    """
        % ",".join(CAPABILITIES[TypeOfUser.RDU_USER])
    )

    op.execute(
        """
          UPDATE users
          SET capabilities = '{INTERNAL_USER, ADMIN}'
          WHERE capabilities = '{%s}'
      """
        % ",".join(CAPABILITIES[TypeOfUser.ADMIN_USER])
    )

    op.execute(
        """
          UPDATE users
          SET capabilities = '{INTERNAL_USER, ADMIN, DEVELOPER}'
          WHERE capabilities = '{%s}'
      """
        % ",".join(CAPABILITIES[TypeOfUser.DEV_USER])
    )

    op.execute(
        """
              UPDATE users
              SET capabilities = '{DEPARTMENTAL_USER}'
              WHERE capabilities = '{%s}'
          """
        % ",".join(CAPABILITIES[TypeOfUser.DEPT_USER])
    )

    op.drop_column("users", "user_type")
    op.execute("DROP TYPE type_of_user_types")

    op.drop_table("user_page")
