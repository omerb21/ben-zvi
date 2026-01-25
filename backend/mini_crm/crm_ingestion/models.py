"""
Database models for the Mini CRM application.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Client(Base):
    """Client model representing a client in the CRM system."""
    __tablename__ = 'client'
    
    id = Column(Integer, primary_key=True)
    id_canon = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    
    def __str__(self):
        return f"Client({self.id_canon}, {self.name})"

class ProductSnapshot(Base):
    """ProductSnapshot model representing a snapshot of a client's product."""
    __tablename__ = 'snapshot'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('client.id'), nullable=False)
    fund_code = Column(String, nullable=False)
    fund_type = Column(String, nullable=True)
    fund_name = Column(String, nullable=True)
    amount = Column(Float, nullable=False, info={'check_constraints': [{'name': 'amount_positive', 'sqltext': 'amount > 0'}]})
    snapshot_date = Column(String, nullable=False)
    
    def __str__(self):
        return f"ProductSnapshot({self.fund_code}, {self.fund_type}, {self.fund_name}, {self.amount}, {self.snapshot_date})"
