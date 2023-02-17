"""empty message

Revision ID: 9dfd2228f643
Revises: 
Create Date: 2023-01-30 18:06:00.712882

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9dfd2228f643'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=60), nullable=True),
    sa.Column('email', sa.String(length=200), nullable=True),
    sa.Column('password', sa.Text(), nullable=True),
    sa.Column('roles', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
    sa.Column('last_login', sa.String(length=20), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user')),
    sa.UniqueConstraint('email', name=op.f('uq_user_email')),
    sa.UniqueConstraint('username', name=op.f('uq_user_username'))
    )
    op.create_table('celery_task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('source', sa.String(length=100), nullable=True),
    sa.Column('destination', sa.String(length=100), nullable=True),
    sa.Column('log_path', sa.String(), nullable=True),
    sa.Column('task_id', sa.String(), nullable=True),
    sa.Column('n_accounts', sa.Integer(), nullable=True),
    sa.Column('domain', sa.String(length=100), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], name=op.f('fk_celery_task_owner_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_celery_task'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('celery_task')
    op.drop_table('user')
    # ### end Alembic commands ###
