from datetime import date

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class ClientBeneficiary(Base):
    """Beneficiary details for a client (used for CRM and justification kits)."""

    __tablename__ = "client_beneficiary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False, index=True)

    # 1-based index of the beneficiary (1..4)
    index = Column(Integer, nullable=False)

    # Allow partial data saving
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    id_number = Column(String(20), nullable=True)
    birth_date = Column(Date, nullable=True)
    address = Column(String(200), nullable=True)
    relation = Column(String(100), nullable=True)
    percentage = Column(Float, nullable=True)

    client = relationship("Client", back_populates="beneficiaries")
