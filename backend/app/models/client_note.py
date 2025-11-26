from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class ClientNote(Base):
    """CRM note/reminder attached to a client."""

    __tablename__ = "client_note"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)

    note = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    reminder_at = Column(String, nullable=True)
    dismissed_at = Column(String, nullable=True)

    client = relationship("Client", back_populates="client_notes")
