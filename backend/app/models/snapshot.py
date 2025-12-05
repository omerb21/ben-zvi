from sqlalchemy import Boolean, Column, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Snapshot(Base):
    """Snapshot of a client's product position (imported from mini_crm)."""

    __tablename__ = "snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False, index=True)

    fund_code = Column(String, nullable=False)
    fund_type = Column(String, nullable=True)
    fund_name = Column(String, nullable=True)
    fund_number = Column(String, nullable=True)
    source = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    snapshot_date = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Indexes for common queries
    __table_args__ = (
        Index("ix_snapshot_client_active", "client_id", "is_active"),
        Index("ix_snapshot_client_date", "client_id", "snapshot_date"),
    )

    client = relationship("Client", back_populates="snapshots")
