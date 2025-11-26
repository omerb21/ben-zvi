from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ClientSignatureRequest(Base):
    """One-time signing request for a client's packet PDF."""

    __tablename__ = "client_signature_request"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)

    token = Column(String(128), nullable=False, unique=True, index=True)
    packet_filename = Column(String(255), nullable=False)
    signed_packet_filename = Column(String(255), nullable=True)

    status = Column(String(32), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    signed_at = Column(DateTime(timezone=True), nullable=True)

    client = relationship("Client", back_populates="signature_requests")
