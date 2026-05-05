import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
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


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    amount = Column(Float)
    category = Column(String)
    description = Column(String, nullable=False)
    date = Column(DateTime, default=datetime.now)
    confidence_score = Column(Float)
    flagged = Column(Boolean, default=False)

    spender = relationship("User", back_populates="expenses")


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    category = Column(String)
    month = Column(DateTime)
    limit = Column(Float)

    spender = relationship("User", back_populates="budgets")

    __table_args__ = (UniqueConstraint("user_id", "category", "month"),)
