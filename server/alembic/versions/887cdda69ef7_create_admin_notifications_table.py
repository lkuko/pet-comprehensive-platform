"""create admin_notifications table

Revision ID: 887cdda69ef7
Revises: bc1cd195fec0
Create Date: 2026-11-14 13:32:06.648397

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '887cdda69ef7'
down_revision: Union[str, None] = 'bc1cd195fec0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('admin_notifications',
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('business_type', sa.String(length=30), nullable=False),
    sa.Column('business_id', sa.BigInteger(), nullable=False),
    sa.Column('title', sa.String(length=100), nullable=False),
    sa.Column('content', sa.String(length=500), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_admin_notifications_business_type', 'admin_notifications', ['business_type'], unique=False)
    op.create_index('ix_admin_notifications_business_id', 'admin_notifications', ['business_id'], unique=False)
    op.create_index('ix_admin_notifications_read', 'admin_notifications', ['is_read', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_admin_notifications_read', table_name='admin_notifications')
    op.drop_index('ix_admin_notifications_business_id', table_name='admin_notifications')
    op.drop_index('ix_admin_notifications_business_type', table_name='admin_notifications')
    op.drop_table('admin_notifications')
