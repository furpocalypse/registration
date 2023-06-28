"""Add email_auth table

Revision ID: ce9b5f903ab7
Revises: dacb9b683ce1
Create Date: 2023-06-27 21:46:35.226815

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "ce9b5f903ab7"
down_revision = "dacb9b683ce1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "email_auth",
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("date_created", sa.DateTime(timezone=True), nullable=False),
        sa.Column("date_expires", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=12), nullable=True),
        sa.PrimaryKeyConstraint("email", name=op.f("pk_email_auth")),
    )
    op.create_index(
        "uq_email_auth_lower_email",
        "email_auth",
        [sa.text("lower('email')")],
        unique=True,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("uq_email_auth_lower_email", table_name="email_auth")
    op.drop_table("email_auth")
    # ### end Alembic commands ###
