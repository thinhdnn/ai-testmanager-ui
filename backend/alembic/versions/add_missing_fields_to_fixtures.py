"""Add missing fields to fixtures table

Revision ID: add_missing_fields_to_fixtures
Revises: update_steps_table_fixture_fields
Create Date: 2025-01-16 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_missing_fields_to_fixtures'
down_revision = 'update_steps_table_fixture_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing fields to fixtures table if they don't exist
    # Check if columns exist before adding them to avoid conflicts
    
    # Get connection and inspector
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Get existing columns
    existing_columns = [col['name'] for col in inspector.get_columns('fixtures')]
    
    # Add updated_by if it doesn't exist
    if 'updated_by' not in existing_columns:
        op.add_column('fixtures', sa.Column('updated_by', sa.String(), nullable=True))
    
    # Add filename if it doesn't exist
    if 'filename' not in existing_columns:
        op.add_column('fixtures', sa.Column('filename', sa.String(), nullable=True))
    
    # Add export_name if it doesn't exist
    if 'export_name' not in existing_columns:
        op.add_column('fixtures', sa.Column('export_name', sa.String(), nullable=True))
    
    # Add fixture_file_path if it doesn't exist
    if 'fixture_file_path' not in existing_columns:
        op.add_column('fixtures', sa.Column('fixture_file_path', sa.String(), nullable=True))
    
    # Add status if it doesn't exist
    if 'status' not in existing_columns:
        op.add_column('fixtures', sa.Column('status', sa.String(), nullable=True, server_default='draft'))
    
    # Add environment if it doesn't exist
    if 'environment' not in existing_columns:
        op.add_column('fixtures', sa.Column('environment', sa.String(), nullable=True, server_default='all'))


def downgrade():
    # Remove added fields from fixtures table
    op.drop_column('fixtures', 'environment')
    op.drop_column('fixtures', 'status')
    op.drop_column('fixtures', 'fixture_file_path')
    op.drop_column('fixtures', 'export_name')
    op.drop_column('fixtures', 'filename')
    op.drop_column('fixtures', 'updated_by')
