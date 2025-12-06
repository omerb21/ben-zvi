"""Add snapshot_date column to existing_product table.

Revision ID: 003_snapshot_date_existing
Revises: 002_add_indexes
Create Date: 2025-12-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003_snapshot_date_existing"
down_revision = "002_add_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Be defensive: the Neon schema may already have this column/index.
    # Use IF NOT EXISTS so the migration is safe to run multiple times.

    # Add column if it does not exist
    op.execute(
        sa.text(
            "ALTER TABLE existing_product "
            "ADD COLUMN IF NOT EXISTS snapshot_date VARCHAR"
        )
    )

    # Create index if it does not exist
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_existing_product_snapshot_date "
            "ON existing_product (snapshot_date)"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_existing_product_snapshot_date", table_name="existing_product")
    op.drop_column("existing_product", "snapshot_date")
