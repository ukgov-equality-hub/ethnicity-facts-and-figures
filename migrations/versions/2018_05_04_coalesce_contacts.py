"""Make contact details 2 per page rather than 2 per source

Revision ID: 2018_05_04_coalesce_contacts
Revises: 2018_04_25_migrate_geog_view
Create Date: 2018-05-04 11:36:02.088310

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2018_05_04_coalesce_contacts'
down_revision = '2018_04_25_migrate_geog_view'
branch_labels = None
depends_on = None


def upgrade():
    # Create new columns for second page-level contact details
    op.add_column('page', sa.Column('contact_2_email', sa.String(length=255), nullable=True))
    op.add_column('page', sa.Column('contact_2_name', sa.String(length=255), nullable=True))
    op.add_column('page', sa.Column('contact_2_phone', sa.String(length=255), nullable=True))

    # Copy any existing second contact details into the new columns from wherever it can be found
    # There is currently no data in any of the "secondary_source_1_contact_2_..." fields, so ignore these
    op.get_bind()
    op.execute("""
        UPDATE page
        SET contact_2_email = subquery.email,
            contact_2_name = subquery.name,
            contact_2_phone = subquery.phone
        FROM (SELECT 
                  guid, 
                  version, 
                  COALESCE(NULLIF(primary_source_contact_2_email,''),NULLIF(secondary_source_1_contact_1_email,''))
                      AS email,
                  COALESCE(NULLIF(primary_source_contact_2_name,''),NULLIF(secondary_source_1_contact_1_name,''))
                      AS name,
                  COALESCE(NULLIF(primary_source_contact_2_phone,''),NULLIF(secondary_source_1_contact_1_phone,''))
                      AS phone
              FROM page
        ) AS subquery
        WHERE page.guid = subquery.guid AND page.version = subquery.version;
    """)

    # Drop the source-related contact columns
    op.drop_column('page', 'primary_source_contact_2_name')
    op.drop_column('page', 'primary_source_contact_2_email')
    op.drop_column('page', 'primary_source_contact_2_phone')
    op.drop_column('page', 'secondary_source_1_contact_1_name')
    op.drop_column('page', 'secondary_source_1_contact_1_email')
    op.drop_column('page', 'secondary_source_1_contact_1_phone')
    op.drop_column('page', 'secondary_source_1_contact_2_name')
    op.drop_column('page', 'secondary_source_1_contact_2_email')
    op.drop_column('page', 'secondary_source_1_contact_2_phone')



def downgrade():
    # We can re-add the previously dropped columns but there is no way to populate them with the "Contact 2" data
    op.add_column('page', sa.Column('primary_source_contact_2_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('primary_source_contact_2_email', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('primary_source_contact_2_phone', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_1_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_1_email', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_1_phone', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_2_name', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_2_email', sa.TEXT(), autoincrement=False, nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_contact_2_phone', sa.TEXT(), autoincrement=False, nullable=True))

    # Drop the "Contact 2" columns, losing all "Contact 2" data
    op.drop_column('page', 'contact_2_phone')
    op.drop_column('page', 'contact_2_name')
    op.drop_column('page', 'contact_2_email')
