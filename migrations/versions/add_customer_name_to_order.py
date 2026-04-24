"""Add customer_name field to Order model for Telegram notifications

Revision ID: add_customer_name_to_order
Revises: 
Create Date: 2026-04-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_customer_name_to_order'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add customer_name column to order table
    op.add_column('order', sa.Column('customer_name', sa.String(100), nullable=True))


def downgrade():
    # Remove customer_name column from order table
    op.drop_column('order', 'customer_name')
