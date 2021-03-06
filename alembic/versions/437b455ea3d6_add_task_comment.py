"""Add task comment

Revision ID: 437b455ea3d6
Revises: 057834a5297b
Create Date: 2021-05-29 19:55:57.885245+00:00

"""
import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision = "437b455ea3d6"
down_revision = "057834a5297b"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("tasks", sa.Column("comment", sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("tasks", "comment")
    # ### end Alembic commands ###
