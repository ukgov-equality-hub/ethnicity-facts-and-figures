"""One migration to recreate our tables from scratch

Revision ID: 2018_06_15_rebase_migration
Revises: None
Create Date: 2018-06-15 08:47:32.766803

"""
import csv

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY

from application.dashboard.view_sql import (
    drop_all_dashboard_helper_views,
    latest_published_pages_view,
    pages_by_geography_view,
    ethnic_groups_by_dimension_view,
    categorisations_by_dimension
)

# revision identifiers, used by Alembic.
revision = '2018_06_15_rebase_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():

    type_of_data_types = sa.Enum('ADMINISTRATIVE', 'SURVEY', name='type_of_data_types')
    type_of_data_types.create(op.get_bind())

    type_of_user_types = sa.Enum('RDU_USER', 'DEPT_USER', 'ADMIN_USER', 'DEV_USER', name='type_of_user_types')
    type_of_user_types.create(op.get_bind())

    type_of_organisation_types = sa.Enum('MINISTERIAL_DEPARTMENT',
                                         'NON_MINISTERIAL_DEPARTMENT',
                                         'EXECUTIVE_OFFICE',
                                         'EXECUTIVE_AGENCY',
                                         'DEVOLVED_ADMINISTRATION',
                                         'COURT',
                                         'TRIBUNAL_NON_DEPARTMENTAL_PUBLIC_BODY',
                                         'CIVIL_SERVICE',
                                         'EXECUTIVE_NON_DEPARTMENTAL_PUBLIC_BODY',
                                         'INDEPENDENT_MONITORING_BODY',
                                         'PUBLIC_CORPORATION',
                                         'SUB_ORGANISATION',
                                         'AD_HOC_ADVISORY_GROUP',
                                         'ADVISORY_NON_DEPARTMENTAL_PUBLIC_BODY',
                                         'OTHER',
                                         name='type_of_organisation_types')

    type_of_organisation_types.create(op.get_bind())

    build_status = sa.Enum('PENDING', 'STARTED', 'DONE', 'SUPERSEDED', 'FAILED', name='build_status')
    build_status.create(op.get_bind())

    uk_country_types = sa.Enum('ENGLAND', 'WALES', 'SCOTLAND', 'NORTHERN_IRELAND', 'UK', name='uk_country_types')
    uk_country_types.create(op.get_bind())

    op.create_table('build',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('succeeded_at', sa.DateTime(), nullable=True),
        sa.Column('failure_reason', sa.String(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', 'created_at', name='build_pkey')
    )
    op.add_column('build', sa.Column('status', build_status, nullable=False))

    op.create_table('categorisation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('family', sa.String(length=255), nullable=True),
        sa.Column('subfamily', sa.String(length=255), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('categorisation_value',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('frequency_of_release',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('lowest_level_of_geography',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('name')
    )
    op.create_table('organisation',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('other_names', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('abbreviations', postgresql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.add_column('organisation', sa.Column('organisation_type', type_of_organisation_types, nullable=False))

    op.create_table('type_of_statistic',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('internal', sa.String(), nullable=False),
        sa.Column('external', sa.String(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('password', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('capabilities', postgresql.ARRAY(sa.String()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.add_column('users', sa.Column('user_type', type_of_user_types, nullable=False))

    op.create_table('association',
    sa.Column('categorisation_id', sa.Integer(), nullable=True),
        sa.Column('categorisation_value_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['categorisation_id'], ['categorisation.id'], name='categorisation_association_fkey'),
        sa.ForeignKeyConstraint(['categorisation_value_id'], ['categorisation_value.id'], name='categorisation_value_association_fkey')
    )

    op.create_table('page',
        sa.Column('guid', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('internal_reference', sa.String(), nullable=True),
        sa.Column('latest', sa.Boolean(), nullable=True),
        sa.Column('uri', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('page_type', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=255), nullable=True),
        sa.Column('publication_date', sa.Date(), nullable=True),
        sa.Column('published', sa.BOOLEAN(), nullable=True),
        sa.Column('parent_guid', sa.String(length=255), nullable=True),
        sa.Column('parent_version', sa.String(), nullable=True),
        sa.Column('db_version_id', sa.Integer(), nullable=False),
        sa.Column('measure_summary', sa.TEXT(), nullable=True),
        sa.Column('summary', sa.TEXT(), nullable=True),
        sa.Column('lowest_level_of_geography_id', sa.String(length=255), nullable=True),
        sa.Column('time_covered', sa.String(length=255), nullable=True),
        sa.Column('need_to_know', sa.TEXT(), nullable=True),
        sa.Column('ethnicity_definition_summary', sa.TEXT(), nullable=True),
        sa.Column('related_publications', sa.TEXT(), nullable=True),
        sa.Column('methodology', sa.TEXT(), nullable=True),
        sa.Column('qmi_url', sa.TEXT(), nullable=True),
        sa.Column('further_technical_information', sa.TEXT(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('external_edit_summary', sa.TEXT(), nullable=True),
        sa.Column('internal_edit_summary', sa.TEXT(), nullable=True),
        sa.Column('source_text', sa.TEXT(), nullable=True),
        sa.Column('type_of_statistic_id', sa.Integer(), nullable=True),
        sa.Column('department_source_text', sa.TEXT(), nullable=True),
        sa.Column('department_source_id', sa.String(length=255), nullable=True),
        sa.Column('source_url', sa.TEXT(), nullable=True),
        sa.Column('published_date', sa.String(length=255), nullable=True),
        sa.Column('note_on_corrections_or_updates', sa.TEXT(), nullable=True),
        sa.Column('frequency_id', sa.Integer(), nullable=True),
        sa.Column('frequency_other', sa.String(length=255), nullable=True),
        sa.Column('data_source_purpose', sa.TEXT(), nullable=True),
        sa.Column('suppression_and_disclosure', sa.TEXT(), nullable=True),
        sa.Column('estimation', sa.TEXT(), nullable=True),
        sa.Column('secondary_source_1_title', sa.TEXT(), nullable=True),
        sa.Column('secondary_source_1_publisher_id', sa.String(length=255), nullable=True),
        sa.Column('secondary_source_1_url', sa.TEXT(), nullable=True),
        sa.Column('secondary_source_1_date', sa.TEXT(), nullable=True),
        sa.Column('secondary_source_1_note_on_corrections_or_updates', sa.TEXT(), nullable=True),
        sa.Column('secondary_source_1_frequency_id', sa.Integer(), nullable=True),
        sa.Column('secondary_source_1_frequency_other', sa.String(length=255), nullable=True),
        sa.Column('secondary_source_1_data_source_purpose', sa.TEXT(), nullable=True),
        sa.Column('secondary_source_1_type_of_statistic_id', sa.Integer(), nullable=True),
        sa.Column('contact_name', sa.TEXT(), nullable=True),
        sa.Column('contact_phone', sa.TEXT(), nullable=True),
        sa.Column('contact_email', sa.TEXT(), nullable=True),
        sa.Column('contact_2_name', sa.TEXT(), nullable=True),
        sa.Column('contact_2_phone', sa.TEXT(), nullable=True),
        sa.Column('contact_2_email', sa.TEXT(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.Column('additional_description', sa.TEXT(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=True),
        sa.Column('last_updated_by', sa.String(length=255), nullable=True),
        sa.Column('published_by', sa.String(length=255), nullable=True),
        sa.Column('unpublished_by', sa.String(length=255), nullable=True),
        sa.Column('review_token', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['department_source_id'], ['organisation.id'], name='page_department_source_id_fkey'),
        sa.ForeignKeyConstraint(['frequency_id'], ['frequency_of_release.id'], name='page_frequency_id_fkey'),
        sa.ForeignKeyConstraint(['lowest_level_of_geography_id'], ['lowest_level_of_geography.name'], name='page_lowest_level_of_geography_id_fkey'),
        sa.ForeignKeyConstraint(['parent_guid', 'parent_version'], ['page.guid', 'page.version'], ),
        sa.ForeignKeyConstraint(['secondary_source_1_frequency_id'], ['frequency_of_release.id'], name='frequency_secondary_source_1_fkey'),
        sa.ForeignKeyConstraint(['secondary_source_1_publisher_id'], ['organisation.id'], name='organisation_secondary_source_1_fkey'),
        sa.ForeignKeyConstraint(['secondary_source_1_type_of_statistic_id'], ['type_of_statistic.id'], name='page_secondary_source_1_type_of_statistic_id_fkey'),
        sa.ForeignKeyConstraint(['type_of_statistic_id'], ['type_of_statistic.id'], name='page_type_of_statistic_id_fkey'),
        sa.PrimaryKeyConstraint('guid', 'version', name='page_guid_version_pk'),
        sa.UniqueConstraint('guid', 'version', name='uix_page_guid_version')
    )
    op.add_column('page', sa.Column('area_covered', ARRAY(uk_country_types), nullable=True))
    op.add_column('page', sa.Column('type_of_data', ARRAY(type_of_data_types), nullable=True))
    op.add_column('page', sa.Column('secondary_source_1_type_of_data', ARRAY(type_of_data_types), nullable=True))

    op.create_table('parent_association',
        sa.Column('categorisation_id', sa.Integer(), nullable=True),
        sa.Column('categorisation_value_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['categorisation_id'], ['categorisation.id'], name='parent_association_categorisation_id_fkey'),
        sa.ForeignKeyConstraint(['categorisation_value_id'], ['categorisation_value.id'], name='parent_association_categorisation_value_id_fkey')
    )

    op.create_table('user_page',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('page_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='user_page_user_id_fkey'),
        sa.PrimaryKeyConstraint('user_id', 'page_id')
    )

    op.create_table('dimension',
        sa.Column('guid', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('time_period', sa.String(length=255), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('chart', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('table', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('chart_source_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('table_source_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('page_id', sa.String(length=255), nullable=False),
        sa.Column('page_version', sa.String(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['page_id', 'page_version'], ['page.guid', 'page.version']),
        sa.PrimaryKeyConstraint('guid')
    )
    op.create_table('upload',
        sa.Column('guid', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('size', sa.String(length=255), nullable=True),
        sa.Column('page_id', sa.String(length=255), nullable=False),
        sa.Column('page_version', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['page_id', 'page_version'], ['page.guid', 'page.version'], ),
        sa.PrimaryKeyConstraint('guid')
    )
    op.create_table('dimension_categorisation',
        sa.Column('dimension_guid', sa.String(length=255), nullable=False),
        sa.Column('categorisation_id', sa.Integer(), nullable=False),
        sa.Column('includes_parents', sa.Boolean(), nullable=True),
        sa.Column('includes_all', sa.Boolean(), nullable=True),
        sa.Column('includes_unknown', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['categorisation_id'], ['categorisation.id'], name='dimension_categorisation_dimension_guid_fkey'),
        sa.ForeignKeyConstraint(['dimension_guid'], ['dimension.guid'], name='dimension_categorisation_categorisation_id_fkey'),
        sa.PrimaryKeyConstraint('dimension_guid', 'categorisation_id')
    )


    op.get_bind()
    op.execute('''
        INSERT INTO lowest_level_of_geography (name, position) VALUES ('United Kingdom', 1);
        INSERT INTO lowest_level_of_geography (name, description, position) VALUES ('Country', '(e.g. England, England and Wales, Scotland...)', 2);
        INSERT INTO lowest_level_of_geography (name, description, position) VALUES ('Region', '(e.g. South West, London, North West, Wales...)', 3);
        INSERT INTO lowest_level_of_geography (name, description, position) VALUES ('Local authority upper', '(e.g. County councils and unitary authorities)', 4);
        INSERT INTO lowest_level_of_geography (name, description, position) VALUES ('Local authority lower', '(e.g. District councils and unitary authorities)', 5);
        INSERT INTO lowest_level_of_geography (name, position) VALUES ('Police force area', 6);
        INSERT INTO lowest_level_of_geography (name, position) VALUES ('Clinical commissioning group', 7);
    ''')

    op.execute('''
        INSERT INTO frequency_of_release (id, position, description) VALUES (1, 1, 'Monthly');
        INSERT INTO frequency_of_release (id, position, description) VALUES (2, 2, 'Quarterly');
        INSERT INTO frequency_of_release (id, position, description) VALUES (3, 3, '3 times a year');
        INSERT INTO frequency_of_release (id, position, description) VALUES (4, 4, 'Twice a year');
        INSERT INTO frequency_of_release (id, position, description) VALUES (5, 5, 'Yearly');
        INSERT INTO frequency_of_release (id, position, description) VALUES (6, 6, 'Every 2 years');
        INSERT INTO frequency_of_release (id, position, description) VALUES (7, 7, 'Every 3 years');
        INSERT INTO frequency_of_release (id, position, description) VALUES (8, 8, 'Every 4 years');
        INSERT INTO frequency_of_release (id, position, description) VALUES (9, 9, 'Every 5 years');
        INSERT INTO frequency_of_release (id, position, description) VALUES (10, 10, 'Ad-hoc');
        INSERT INTO frequency_of_release (id, position, description) VALUES (11, 11, 'Other');
    ''')

    op.execute('''
      INSERT INTO type_of_statistic (id, internal, external, position)
      VALUES (1, 'National Statistics (certified against a Code of Practice)', 'National Statistics', 1);
    ''')
    op.execute('''
      INSERT INTO type_of_statistic (id, internal, external, position)
      VALUES (2, 'Official statistics (any other government statistics)', 'Official statistics', 2);
    ''')
    op.execute('''
      INSERT INTO type_of_statistic (id, internal, external, position)
      VALUES (3, 'Experimental statistics', 'Experimental statistics', 3);
    ''')

    op.execute('''
      INSERT INTO type_of_statistic (id, internal, external, position)
      VALUES (4, 'Non-official statistics (not produced by a Government department or agency)', 'Non-official statistics', 4);
    ''')

    with open('./application/data/organisations.csv') as orgs_file:
        reader = csv.DictReader(orgs_file)
        for row in reader:
            if not row.get('end_date'):
                other_names = row.get('other_names')
                if other_names is not None:
                    other_names = other_names.replace("'", "''")

                abbreviations = row.get('abbreviations')
                if abbreviations is not None:
                    abbreviations = abbreviations.replace("'", "''")

                insert_sql = "INSERT INTO organisation (id, name, other_names, abbreviations, organisation_type) VALUES (\'%s\', \'%s\', \'{%s}\', \'{%s}\', \'%s\');" % (
                row['id'].strip(),
                row['name'].strip().replace("'", "''"),
                other_names,
                abbreviations,
                row['organisation_type'].strip().replace(' ', '_').replace('-', '_').upper())

                op.execute(insert_sql)

    from bootstrap_sql import initial_data
    op.execute(initial_data)

    op.execute(latest_published_pages_view)
    op.execute(pages_by_geography_view)
    op.execute(ethnic_groups_by_dimension_view)
    op.execute(categorisations_by_dimension)


def downgrade():

    op.execute(drop_all_dashboard_helper_views)
    op.drop_table('dimension_categorisation')
    op.drop_table('upload')
    op.drop_table('dimension')
    op.drop_table('user_page')
    op.drop_table('parent_association')
    op.drop_table('page')
    op.drop_table('association')
    op.drop_table('users')
    op.drop_table('type_of_statistic')
    op.drop_table('organisation')
    op.drop_table('lowest_level_of_geography')
    op.drop_table('frequency_of_release')
    op.drop_table('categorisation_value')
    op.drop_table('categorisation')
    op.drop_table('build')

    op.execute('DROP TYPE type_of_data_types')
    op.execute('DROP TYPE type_of_user_types')
    op.execute('DROP TYPE uk_country_types')
    op.execute('DROP TYPE type_of_organisation_types')
    op.execute('DROP TYPE build_status')
