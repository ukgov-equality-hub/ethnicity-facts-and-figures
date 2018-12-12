"""Add topic, subtopic and measure tables plus subtopic_measure relationship table

Revision ID: 20181211_topic_subtopic_measure
Revises: 2018_12_05_not_nullable_fields
Create Date: 2018-12-11 13:11:47.567135

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20181211_topic_subtopic_measure"
down_revision = "2018_12_05_not_nullable_fields"
branch_labels = None
depends_on = None


def upgrade():

    op.create_table(
        "measure",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uri", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("reference", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("measure_pkey")),
    )

    op.create_table(
        "topic",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uri", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("additional_description", sa.TEXT(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("topic_pkey")),
    )

    op.create_table(
        "subtopic",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("uri", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("topic_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["topic_id"], ["topic.id"], name=op.f("subtopic_topic_id_fkey")),
        sa.PrimaryKeyConstraint("id", name=op.f("subtopic_pkey")),
    )

    op.create_table(
        "subtopic_measure",
        sa.Column("subtopic_id", sa.Integer(), nullable=False),
        sa.Column("measure_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["measure_id"], ["measure.id"], name=op.f("subtopic_measure_measure_id_fkey")),
        sa.ForeignKeyConstraint(["subtopic_id"], ["subtopic.id"], name=op.f("subtopic_measure_subtopic_id_fkey")),
        sa.PrimaryKeyConstraint("subtopic_id", "measure_id", name=op.f("subtopic_measure_pkey")),
    )


def downgrade():
    op.drop_table("subtopic_measure")
    op.drop_table("subtopic")
    op.drop_table("topic")
    op.drop_table("measure")
