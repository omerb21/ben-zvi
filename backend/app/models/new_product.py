from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class NewProduct(Base):
    """New product created for a client as part of justification flow."""

    __tablename__ = "new_product"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False)
    existing_product_id = Column(Integer, ForeignKey("existing_product.id"), nullable=True)

    # Copied fields from existing product
    fund_type = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    fund_name = Column(String, nullable=False)
    fund_code = Column(String, nullable=False)
    yield_1yr = Column(Float, nullable=True)
    yield_3yr = Column(Float, nullable=True)

    # Non-editable fields
    personal_number = Column(String, nullable=True, unique=True)
    management_fee_balance = Column(Float, nullable=True)
    management_fee_contributions = Column(Float, nullable=True)
    accumulated_amount = Column(Float, nullable=True)
    employment_status = Column(String, nullable=True)
    has_regular_contributions = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    client = relationship("Client", back_populates="new_products")
    existing_product = relationship("ExistingProduct", back_populates="new_products")
    form_instances = relationship(
        "FormInstance",
        back_populates="new_product",
        cascade="all, delete-orphan",
    )
