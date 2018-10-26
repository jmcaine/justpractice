"""added email address to User

Revision ID: 7576f76db98b
Revises: 4df376d8904d
Create Date: 2018-09-30 01:46:50.451912

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7576f76db98b'
down_revision = '4df376d8904d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('email', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'email')
    # ### end Alembic commands ###
