from datetime import datetime, timezone
from typing import Annotated, Literal, TypedDict

from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class ExtractedExpense(BaseModel):
    amount: float | None = None
    category: (
        Literal["Food", "Transport", "Shopping", "Utilities", "Entertainment", "Others"]
        | None
    ) = None
    description: str | None = None
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence_score: float = Field(ge=0.0, le=1.0)


class ExpenseAgentState(TypedDict):
    user_id: str
    messages: Annotated[list, add_messages]
    extracted_info: ExtractedExpense
    flagged: bool
    flagged_reason: str
    iterations: int
