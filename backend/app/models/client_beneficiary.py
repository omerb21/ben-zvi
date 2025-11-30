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

    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    id_number = Column(String(20), nullable=False)
    birth_date = Column(Date, nullable=False)
    address = Column(String(200), nullable=False)
    relation = Column(String(100), nullable=False)
    percentage = Column(Float, nullable=False)

    client = relationship("Client", back_populates="beneficiaries")
