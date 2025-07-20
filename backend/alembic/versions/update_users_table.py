"""Update users table for fastapi-users

Revision ID: update_users_table
Revises: 
Create Date: 2025-07-19 15:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'update_users_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column('users', sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False))
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=True, default=False))
    
    # Rename password column to hashed_password
    op.alter_column('users', 'password', new_column_name='hashed_password')
    
    # Make email not nullable
    op.alter_column('users', 'email', nullable=False)


def downgrade() -> None:
    # Make email nullable again
    op.alter_column('users', 'email', nullable=True)
    
    # Rename hashed_password back to password
    op.alter_column('users', 'hashed_password', new_column_name='password')
    
    # Drop new columns
    op.drop_column('users', 'is_superuser')
    op.drop_column('users', 'is_verified') 