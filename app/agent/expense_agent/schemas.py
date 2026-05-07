from datetime import datetime, timezone
from typing import Literal, TypedDict

from pydantic import BaseModel, Field

from app.schemas.expense_schema import ExpenseCreate


class ExtractedExpense(BaseModel):
    amount: float | None = None
    category: (
        Literal["Food", "Transport", "Shopping", "Utilities", "Entertainment", "Others"]
        | None
    ) = None
    extracted_description: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence_score: float = Field(ge=0.0, le=1.0)


class ExpenseAgentState(TypedDict):
    input: ExpenseCreate
    extracted_info: ExtractedExpense
    flagged: bool
    flagged_reason: str
    iterations: int
