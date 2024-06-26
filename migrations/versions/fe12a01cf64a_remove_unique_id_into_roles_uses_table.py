"""Remove unique id into roles_uses table

Revision ID: fe12a01cf64a
Revises: 8ddd237ecdd6
Create Date: 2024-02-12 14:05:04.646808

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fe12a01cf64a"
down_revision = "8ddd237ecdd6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("roles_users", schema=None) as batch_op:
        batch_op.drop_column("id")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("roles_users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("id", sa.INTEGER(), nullable=False))

    # ### end Alembic commands ###
