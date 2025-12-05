"""Baseline migration - represents existing schema in Neon.

Revision ID: 001_baseline
Revises: 
Create Date: 2025-01-01

This is a baseline migration that represents the schema already existing in Neon.
It does not create any tables since they already exist.
Future migrations should build on top of this baseline.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Baseline migration - no operations needed.
    The following tables already exist in Neon:
    - client
    - snapshot
    - saving_product
    - existing_product
    - new_product
    - form_instance
    - client_note
    - client_signature_request
    - client_beneficiary
    """
    pass


def downgrade() -> None:
    """
    Downgrade is not supported for baseline migration.
    """
    pass
