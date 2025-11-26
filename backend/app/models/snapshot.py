from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Snapshot(Base):
    """Snapshot of a client's product position (imported from mini_crm)."""

    __tablename__ = "snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)

    fund_code = Column(String, nullable=False)
    fund_type = Column(String, nullable=True)
    fund_name = Column(String, nullable=True)
    fund_number = Column(String, nullable=True)
    source = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    snapshot_date = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    client = relationship("Client", back_populates="snapshots")
