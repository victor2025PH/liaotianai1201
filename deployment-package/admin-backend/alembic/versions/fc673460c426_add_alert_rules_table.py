"""add_alert_rules_table

Revision ID: fc673460c426
Revises: 003_add_script_version_management
Create Date: 2025-11-18 04:13:02.534093

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fc673460c426'
down_revision = '003_add_script_version_management'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 創建告警規則表
    op.create_table(
        'group_ai_alert_rules',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False, unique=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('alert_level', sa.String(20), nullable=False, server_default='warning'),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        sa.Column('threshold_operator', sa.String(10), nullable=False, server_default='>'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('notification_method', sa.String(50), server_default='email'),
        sa.Column('notification_target', sa.String(500), nullable=True),
        sa.Column('rule_conditions', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    
    # 創建索引
    op.create_index('ix_group_ai_alert_rules_name', 'group_ai_alert_rules', ['name'])
    op.create_index('ix_group_ai_alert_rules_rule_type', 'group_ai_alert_rules', ['rule_type'])
    op.create_index('ix_group_ai_alert_rules_enabled', 'group_ai_alert_rules', ['enabled'])


def downgrade() -> None:
    # 刪除索引
    op.drop_index('ix_group_ai_alert_rules_enabled', table_name='group_ai_alert_rules')
    op.drop_index('ix_group_ai_alert_rules_rule_type', table_name='group_ai_alert_rules')
    op.drop_index('ix_group_ai_alert_rules_name', table_name='group_ai_alert_rules')
    
    # 刪除表
    op.drop_table('group_ai_alert_rules')

