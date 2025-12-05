"""Add performance indexes to key tables.

Revision ID: 002_add_indexes
Revises: 001_baseline
Create Date: 2025-01-01

Adds indexes to improve query performance on commonly accessed columns.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_indexes'
down_revision = '001_baseline'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add indexes for improved query performance.

    Uses IF NOT EXISTS so running against an already-indexed Neon DB does not fail.
    """

    # Snapshot indexes
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_snapshot_client_id "
            "ON snapshot (client_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_snapshot_client_active "
            "ON snapshot (client_id, is_active)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_snapshot_client_date "
            "ON snapshot (client_id, snapshot_date)"
        )
    )

    # ExistingProduct indexes
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_existing_product_client_id "
            "ON existing_product (client_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_existing_product_personal_number "
            "ON existing_product (personal_number)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_existing_product_client_personal "
            "ON existing_product (client_id, personal_number)"
        )
    )

    # NewProduct indexes
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_new_product_client_id "
            "ON new_product (client_id)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_new_product_existing_product_id "
            "ON new_product (existing_product_id)"
        )
    )

    # FormInstance indexes
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_form_instance_new_product_id "
            "ON form_instance (new_product_id)"
        )
    )

    # ClientBeneficiary indexes
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_client_beneficiary_client_id "
            "ON client_beneficiary (client_id)"
        )
    )


def downgrade() -> None:
    """Remove indexes."""
    
    # ClientBeneficiary indexes
    op.drop_index('ix_client_beneficiary_client_id', table_name='client_beneficiary')
    
    # FormInstance indexes
    op.drop_index('ix_form_instance_new_product_id', table_name='form_instance')
    
    # NewProduct indexes
    op.drop_index('ix_new_product_existing_product_id', table_name='new_product')
    op.drop_index('ix_new_product_client_id', table_name='new_product')
    
    # ExistingProduct indexes
    op.drop_index('ix_existing_product_client_personal', table_name='existing_product')
    op.drop_index('ix_existing_product_personal_number', table_name='existing_product')
    op.drop_index('ix_existing_product_client_id', table_name='existing_product')
    
    # Snapshot indexes
    op.drop_index('ix_snapshot_client_date', table_name='snapshot')
    op.drop_index('ix_snapshot_client_active', table_name='snapshot')
    op.drop_index('ix_snapshot_client_id', table_name='snapshot')
