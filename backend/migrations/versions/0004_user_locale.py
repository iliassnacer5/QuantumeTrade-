"""Ajoute users.locale (i18n — Phase 5). Migration granulaire idempotente.

Revision ID: 0004
Revises: 0003
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    return any(c["name"] == column for c in sa.inspect(op.get_bind()).get_columns(table))


def upgrade() -> None:
    if not _has_column("users", "locale"):
        op.add_column("users", sa.Column("locale", sa.String(), nullable=False, server_default="fr"))


def downgrade() -> None:
    if _has_column("users", "locale"):
        op.drop_column("users", "locale")
