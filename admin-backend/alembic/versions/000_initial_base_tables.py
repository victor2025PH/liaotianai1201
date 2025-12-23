"""創建基礎表（用戶、角色、權限）

Revision ID: 000_initial_base
Revises: 
Create Date: 2025-01-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '000_initial_base'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 檢查表是否存在（用於處理表已存在的情況）
    from sqlalchemy import inspect
    from alembic import context
    
    conn = context.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # 創建用戶表
    if 'users' not in existing_tables:
        op.create_table(
            'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_users_id', 'users', ['id'], unique=False)
        op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # 創建角色表
    if 'roles' not in existing_tables:
        op.create_table(
            'roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_roles_id', 'roles', ['id'], unique=False)
        op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    
    # 創建權限表
    if 'permissions' not in existing_tables:
        op.create_table(
            'permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(128), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_permissions_id', 'permissions', ['id'], unique=False)
        op.create_index(op.f('ix_permissions_code'), 'permissions', ['code'], unique=True)
    
    # 創建用戶-角色關聯表
    if 'user_roles' not in existing_tables:
        op.create_table(
            'user_roles',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
        )
    
    # 創建角色-權限關聯表
    if 'role_permissions' not in existing_tables:
        op.create_table(
            'role_permissions',
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
        )


def downgrade():
    # 刪除關聯表
    op.drop_table('role_permissions')
    op.drop_table('user_roles')
    
    # 刪除基礎表
    op.drop_index('ix_permissions_code', table_name='permissions')
    op.drop_index('ix_permissions_id', table_name='permissions')
    op.drop_table('permissions')
    
    op.drop_index('ix_roles_name', table_name='roles')
    op.drop_index('ix_roles_id', table_name='roles')
    op.drop_table('roles')
    
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')

