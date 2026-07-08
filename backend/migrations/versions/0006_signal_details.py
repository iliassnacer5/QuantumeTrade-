"""Ajoute signals.details (payload complet JSON : agents, news, métriques, mtf…).

Rend chaque prédiction consultable en détail après coup (transparence pour le trader).
Migration granulaire idempotente.

Revision ID: 0006
Revises: 0005
"""

from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    return any(c["name"] == column for c in sa.inspect(op.get_bind()).get_columns(table))


def upgrade() -> None:
    if not _has_column("signals", "details"):
        op.add_column("signals", sa.Column("details", sa.Text(), nullable=True))


def downgrade() -> None:
    if _has_column("signals", "details"):
        op.drop_column("signals", "details")
