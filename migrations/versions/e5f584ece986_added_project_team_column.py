"""Added 'project_team' column

Revision ID: e5f584ece986
Revises: 5c730bcde388
Create Date: 2018-05-22 14:50:34.555860

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5f584ece986'
down_revision = '5c730bcde388'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('project_team', sa.Boolean(), nullable=True))
    op.create_index(op.f('ix_user_project_team'), 'user', ['project_team'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_project_team'), table_name='user')
    op.drop_column('user', 'project_team')
    # ### end Alembic commands ###
