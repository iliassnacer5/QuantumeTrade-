"""Migration initiale — crée toutes les tables ORM (idempotent).

Utilise Base.metadata.create_all(checkfirst=True) : crée les tables manquantes sans toucher aux
existantes, et reste toujours aligné sur les modèles. Les évolutions de schéma ultérieures se font
via des migrations granulaires (op.add_column, ...).

Revision ID: 0001
Revises:
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models.db import Base

    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    from app.models.db import Base

    Base.metadata.drop_all(bind=op.get_bind())
