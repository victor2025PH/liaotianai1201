"""add_account_profile_and_server_fields

Revision ID: ea5d525f9c2a
Revises: fc673460c426
Create Date: 2025-11-18 07:36:56.179627

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea5d525f9c2a'
down_revision = 'fc673460c426'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加服務器關聯字段
    op.add_column('group_ai_accounts', sa.Column('server_id', sa.String(100), nullable=True))
    op.create_index('ix_group_ai_accounts_server_id', 'group_ai_accounts', ['server_id'])
    
    # 添加帳號資料信息字段
    op.add_column('group_ai_accounts', sa.Column('phone_number', sa.String(20), nullable=True))
    op.add_column('group_ai_accounts', sa.Column('username', sa.String(100), nullable=True))
    op.add_column('group_ai_accounts', sa.Column('first_name', sa.String(200), nullable=True))
    op.add_column('group_ai_accounts', sa.Column('last_name', sa.String(200), nullable=True))
    op.add_column('group_ai_accounts', sa.Column('display_name', sa.String(200), nullable=True))
    op.add_column('group_ai_accounts', sa.Column('avatar_url', sa.String(500), nullable=True))
    op.add_column('group_ai_accounts', sa.Column('bio', sa.Text(), nullable=True))
    op.add_column('group_ai_accounts', sa.Column('user_id', sa.BigInteger(), nullable=True))
    op.create_index('ix_group_ai_accounts_user_id', 'group_ai_accounts', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_group_ai_accounts_user_id', table_name='group_ai_accounts')
    op.drop_column('group_ai_accounts', 'user_id')
    op.drop_column('group_ai_accounts', 'bio')
    op.drop_column('group_ai_accounts', 'avatar_url')
    op.drop_column('group_ai_accounts', 'display_name')
    op.drop_column('group_ai_accounts', 'last_name')
    op.drop_column('group_ai_accounts', 'first_name')
    op.drop_column('group_ai_accounts', 'username')
    op.drop_column('group_ai_accounts', 'phone_number')
    op.drop_index('ix_group_ai_accounts_server_id', table_name='group_ai_accounts')
    op.drop_column('group_ai_accounts', 'server_id')
