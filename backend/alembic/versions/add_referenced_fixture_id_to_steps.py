"""add referenced_fixture_id to steps

Revision ID: add_referenced_fixture_id_to_steps
Revises: add_test_case_fixtures_table
Create Date: 2025-01-09 06:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_ref_fixture_to_steps'
down_revision = 'add_test_case_fixtures_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add referenced_fixture_id column to steps table
    op.add_column('steps', sa.Column('referenced_fixture_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_steps_referenced_fixture_id_fixtures',
        'steps', 'fixtures',
        ['referenced_fixture_id'], ['id']
    )


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_steps_referenced_fixture_id_fixtures', 'steps', type_='foreignkey')
    
    # Remove referenced_fixture_id column
    op.drop_column('steps', 'referenced_fixture_id')
