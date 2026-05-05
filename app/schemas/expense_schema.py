from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExpenseBase(BaseModel):
    description: str
    user_id: str


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseResponse(ExpenseBase):
    id: str
    amount: float
    category: str
    date: datetime
    confidence_score: float
    flagged: bool

    model_config = ConfigDict(from_attributes=True)


class ExpenseUpdate(BaseModel):
    amount: float | None = None
    category: str | None = None


class ExpenseFilter(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    less_than_amount: float | None = None
    category: str | None = None
