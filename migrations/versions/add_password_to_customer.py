"""Add password column to customer table

Revision ID: add_password_customer
Revises: add_email_column
Create Date: 2026-03-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_password_customer'
down_revision = 'add_email_column'
branch_labels = None
depends_on = None


def upgrade():
    # Add password column to customer table
    op.add_column('customer', sa.Column('password', sa.String(255), nullable=True))


def downgrade():
    # Remove password column from customer table
    op.drop_column('customer', 'password')
