"""Ajoute users.push_token (notifications push natives — Phase 3).

Migration granulaire (idempotente) au-dessus de la baseline 0001 : ajoute la colonne uniquement si
elle n'existe pas déjà, pour rester compatible avec les bases créées via create_all.

Revision ID: 0002
Revises: 0001
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_column("users", "push_token"):
        op.add_column("users", sa.Column("push_token", sa.String(), nullable=True))


def downgrade() -> None:
    if _has_column("users", "push_token"):
        op.drop_column("users", "push_token")
