import uuid

from sqlalchemy import (
    Column,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    category = Column(String)
    month = Column(String)
    limit = Column(Float)

    spender = relationship("User", back_populates="budgets")

    __table_args__ = (UniqueConstraint("user_id", "category", "month"),)
