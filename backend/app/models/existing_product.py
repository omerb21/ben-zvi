from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class ExistingProduct(Base):
    """Existing product held by a client (from justification system)."""

    __tablename__ = "existing_product"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)

    # Fields from XML
    fund_type = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    fund_name = Column(String, nullable=False)
    fund_code = Column(String, nullable=False)
    yield_1yr = Column(Float, nullable=True)
    yield_3yr = Column(Float, nullable=True)

    # Fields from user
    personal_number = Column(String, nullable=False, unique=True)
    management_fee_balance = Column(Float, nullable=True)
    management_fee_contributions = Column(Float, nullable=True)
    accumulated_amount = Column(Float, nullable=True)
    employment_status = Column(String, nullable=True)
    has_regular_contributions = Column(Boolean, nullable=True)

    client = relationship("Client", back_populates="existing_products")
    new_products = relationship("NewProduct", back_populates="existing_product", cascade="all, delete-orphan")
