"""add telegram registration tables

Revision ID: xxxx_add_telegram_registration
Revises: ccaf23c9b58a
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = 'xxxx_add_telegram_registration'
down_revision = 'ccaf23c9b58a'
branch_labels = None
depends_on = None


def upgrade():
    # 创建 user_registrations 表
    op.create_table(
        'user_registrations',
        sa.Column('id', sa.String(36), primary_key=True),  # SQLite使用字符串存储UUID
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('country_code', sa.String(5), nullable=False),
        sa.Column('api_id', sa.Integer(), nullable=True),
        sa.Column('api_hash', sa.String(64), nullable=True),
        sa.Column('node_id', sa.String(50), nullable=False),
        sa.Column('session_name', sa.String(100), nullable=True),
        sa.Column('session_file_path', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('phone_code_hash', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.datetime('now')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.datetime('now')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('risk_score', sa.Integer(), default=0),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),  # IPv6最长45字符
    )
    
    op.create_index('idx_user_registrations_phone', 'user_registrations', ['phone'])
    op.create_index('idx_user_registrations_status', 'user_registrations', ['status'])
    op.create_index('idx_user_registrations_node_id', 'user_registrations', ['node_id'])
    op.create_index('idx_user_registrations_created_at', 'user_registrations', ['created_at'])
    op.create_index('idx_user_registrations_phone_node', 'user_registrations', ['phone', 'node_id'], unique=True)
    
    # 创建 session_files 表
    op.create_table(
        'session_files',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('registration_id', sa.String(36), sa.ForeignKey('user_registrations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_name', sa.String(100), nullable=False),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_hash', sa.String(64), nullable=True),
        sa.Column('server_node_id', sa.String(50), nullable=False),
        sa.Column('is_encrypted', sa.Boolean(), default=False),
        sa.Column('encryption_key_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.datetime('now')),
        sa.Column('last_verified_at', sa.DateTime(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), default=True),
        sa.Column('extra_metadata', sa.Text(), nullable=True),  # SQLite使用TEXT存储JSON
    )
    
    op.create_index('idx_session_files_registration_id', 'session_files', ['registration_id'])
    op.create_index('idx_session_files_server_node_id', 'session_files', ['server_node_id'])
    op.create_index('idx_session_files_is_valid', 'session_files', ['is_valid'])
    
    # 创建 anti_detection_logs 表
    op.create_table(
        'anti_detection_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('registration_id', sa.String(36), sa.ForeignKey('user_registrations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=True),
        sa.Column('risk_score', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_fingerprint', sa.String(100), nullable=True),
        sa.Column('behavior_pattern', sa.Text(), nullable=True),  # SQLite使用TEXT存储JSON
        sa.Column('action_taken', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.datetime('now')),
    )
    
    op.create_index('idx_anti_detection_logs_registration_id', 'anti_detection_logs', ['registration_id'])
    op.create_index('idx_anti_detection_logs_event_type', 'anti_detection_logs', ['event_type'])
    op.create_index('idx_anti_detection_logs_risk_level', 'anti_detection_logs', ['risk_level'])
    op.create_index('idx_anti_detection_logs_created_at', 'anti_detection_logs', ['created_at'])


def downgrade():
    op.drop_table('anti_detection_logs')
    op.drop_table('session_files')
    op.drop_table('user_registrations')

