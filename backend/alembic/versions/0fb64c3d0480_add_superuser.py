"""add_superuser

Revision ID: 0fb64c3d0480
Revises: update_users_table
Create Date: 2025-07-19 21:56:23.566611

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision = '0fb64c3d0480'
down_revision = 'update_users_table'
branch_labels = None
depends_on = None

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    # Create superuser if not exists
    connection = op.get_bind()
    
    # Check if superuser already exists
    result = connection.execute(sa.text("SELECT COUNT(*) FROM users WHERE email = 'admin@testmanager.com'"))
    count = result.scalar()
    
    if count == 0:
        # Hash the password
        hashed_password = pwd_context.hash("admin123")
        
        # Insert superuser
        connection.execute(sa.text("""
            INSERT INTO users (
                id, 
                email, 
                username, 
                hashed_password, 
                is_active, 
                is_superuser, 
                is_verified, 
                created_at
            ) VALUES (
                :id,
                :email,
                :username,
                :hashed_password,
                :is_active,
                :is_superuser,
                :is_verified,
                NOW()
            )
        """), {
            'id': str(uuid.uuid4()),
            'email': 'admin@testmanager.com',
            'username': 'admin',
            'hashed_password': hashed_password,
            'is_active': True,
            'is_superuser': True,
            'is_verified': True
        })
        
        print("Superuser created successfully!")


def downgrade() -> None:
    # Remove superuser
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM users WHERE email = 'admin@testmanager.com'")) 