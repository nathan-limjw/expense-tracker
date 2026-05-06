import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    String,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    email = Column(String, unique=True)
    monthly_budget = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now)

    expenses = relationship("Expense", back_populates="spender")
    budgets = relationship("Budget", back_populates="spender")
