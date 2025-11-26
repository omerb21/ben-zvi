from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class FormInstance(Base):
    """Filled PDF form instance linked to a new product."""

    __tablename__ = "form_instance"

    id = Column(Integer, primary_key=True)
    new_product_id = Column(Integer, ForeignKey("new_product.id"), nullable=False)
    template_filename = Column(String(255), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(255), nullable=False, default="נוצר")
    filled_data = Column(JSON, nullable=True)
    file_output_path = Column(String(512), nullable=True)

    new_product = relationship("NewProduct", back_populates="form_instances")
