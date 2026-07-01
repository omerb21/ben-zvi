"""Add reference PDF data to signature requests.

Revision ID: 004_signature_reference_pdf
Revises: 003_snapshot_date_existing
Create Date: 2026-07-01

"""
from alembic import op
import sqlalchemy as sa


revision = "004_signature_reference_pdf"
down_revision = "003_snapshot_date_existing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {
        column["name"]
        for column in inspector.get_columns("client_signature_request")
    }
    if "reference_pdf_data" not in columns:
        op.add_column(
            "client_signature_request",
            sa.Column("reference_pdf_data", sa.LargeBinary(), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("client_signature_request", "reference_pdf_data")
