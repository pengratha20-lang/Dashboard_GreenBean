"""Add email column to user table

Revision ID: add_email_column
Revises: 7c5a8223b0b1
Create Date: 2026-02-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_email_column'
down_revision = '7c5a8223b0b1'
branch_labels = None
depends_on = None


def upgrade():
    # Add email column to user table
    op.add_column('user', sa.Column('email', sa.String(120), nullable=True))
    
    # Create a unique constraint on email
    op.create_unique_constraint('uq_user_email', 'user', ['email'])


def downgrade():
    # Remove unique constraint
    op.drop_constraint('uq_user_email', 'user', type_='unique')
    
    # Remove email column
    op.drop_column('user', 'email')
