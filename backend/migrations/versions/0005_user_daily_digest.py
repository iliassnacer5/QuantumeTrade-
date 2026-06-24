"""Ajoute users.daily_digest (automatisation : digest quotidien des trades fiables).

Migration granulaire idempotente.

Revision ID: 0005
Revises: 0004
"""

from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    return any(c["name"] == column for c in sa.inspect(op.get_bind()).get_columns(table))


def upgrade() -> None:
    if not _has_column("users", "daily_digest"):
        op.add_column("users", sa.Column("daily_digest", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    if _has_column("users", "daily_digest"):
        op.drop_column("users", "daily_digest")
