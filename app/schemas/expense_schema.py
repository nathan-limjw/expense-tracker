from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExpenseBase(BaseModel):
    description: str
    user_id: str


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseResponse(ExpenseBase):
    id: str
    amount: float
    category: Literal[
        "Food", "Transport", "Shopping", "Utilities", "Entertainment", "Others"
    ]
    date: datetime
    confidence_score: float
    flagged: bool

    model_config = ConfigDict(from_attributes=True)


class ExpenseCreateResponse(BaseModel):
    expense: ExpenseResponse
    messages: list[str] = []


class ExpenseUpdate(BaseModel):
    amount: float | None = Field(default=None, gt=0)
    category: (
        Literal["Food", "Transport", "Shopping", "Utilities", "Entertainment", "Others"]
        | None
    ) = None


class ExpenseFilter(BaseModel):
    start_date: datetime | None = None
    end_date: datetime | None = None
    less_than_amount: float | None = Field(default=None, gt=0)
    category: (
        Literal["Food", "Transport", "Shopping", "Utilities", "Entertainment", "Others"]
        | None
    ) = None
