"""Add test case fixtures table

Revision ID: add_test_case_fixtures_table
Revises: 0fb64c3d0480
Create Date: 2025-08-09 02:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_test_case_fixtures_table'
down_revision = '0fb64c3d0480'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create test_case_fixtures table
    op.create_table('test_case_fixtures',
        sa.Column('test_case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fixture_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['test_case_id'], ['test_cases.id'], name='test_case_fixtures_test_case_id_fkey'),
        sa.ForeignKeyConstraint(['fixture_id'], ['fixtures.id'], name='test_case_fixtures_fixture_id_fkey'),
        sa.PrimaryKeyConstraint('test_case_id', 'fixture_id', name='test_case_fixtures_pkey')
    )


def downgrade() -> None:
    # Drop test_case_fixtures table
    op.drop_table('test_case_fixtures')
