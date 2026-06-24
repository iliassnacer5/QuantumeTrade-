"""Table générique `records` (document store Phase 4 : broker, ordres, copy-trading, marketplace).

Migration granulaire idempotente au-dessus de 0002.

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def _has_table(name: str) -> bool:
    return sa.inspect(op.get_bind()).has_table(name)


def upgrade() -> None:
    if _has_table("records"):
        return
    op.create_table(
        "records",
        sa.Column("kind", sa.String(), nullable=False),
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tenant_id", sa.String(), nullable=True),
        sa.Column("payload", sa.Text(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("kind", "id"),
    )
    op.create_index("ix_records_tenant_id", "records", ["tenant_id"], unique=False)


def downgrade() -> None:
    if _has_table("records"):
        op.drop_index("ix_records_tenant_id", table_name="records")
        op.drop_table("records")
