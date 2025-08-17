"""Update steps table fixture fields

Revision ID: update_steps_table_fixture_fields
Revises: add_test_case_fixtures_table
Create Date: 2025-08-16 07:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_steps_table_fixture_fields'
down_revision = 'add_test_case_fixtures_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add referenced_fixture_type column
    op.add_column('steps', sa.Column('referenced_fixture_type', sa.String(), nullable=True))
    
    # Update existing steps to set referenced_fixture_type based on fixture type
    # First, get all steps with referenced_fixture_id
    connection = op.get_bind()
    
    # Get steps with referenced fixtures and their types
    result = connection.execute(sa.text("""
        SELECT s.id, f.type 
        FROM steps s 
        JOIN fixtures f ON s.referenced_fixture_id = f.id 
        WHERE s.referenced_fixture_id IS NOT NULL
    """))
    
    # Update each step with the fixture type
    for step_id, fixture_type in result:
        connection.execute(sa.text("""
            UPDATE steps 
            SET referenced_fixture_type = :fixture_type 
            WHERE id = :step_id
        """), {
            'fixture_type': fixture_type,
            'step_id': step_id
        })
    
    # Remove old fixture_id column (after ensuring data is migrated)
    op.drop_column('steps', 'fixture_id')


def downgrade() -> None:
    # Add back fixture_id column
    op.add_column('steps', sa.Column('fixture_id', postgresql.UUID(as_uuid=True), nullable=True))
    
    # Remove referenced_fixture_type column
    op.drop_column('steps', 'referenced_fixture_type')
