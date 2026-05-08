from datetime import datetime, timezone

from app.agent.expense_agent.schemas import ExtractedExpense
from app.schemas.expense_schema import ExpenseCreate


def setup_mock(extracted_expense: ExtractedExpense, mocker, mock_llm):
    extracted_output = extracted_expense

    mock_structured_llm = mocker.MagicMock()
    mock_structured_llm.invoke.return_value = extracted_output

    mock_llm.with_structured_output.return_value = mock_structured_llm


def populate_expense_agent_state(
    description: str = "$2 coffee",
    user_id: str = "kimmy",
    flagged: bool = False,
    flagged_reason: str = None,
    iterations: int = 0,
):
    return {
        "input": ExpenseCreate(description=description, user_id=user_id),
        "flagged": flagged,
        "flagged_reason": flagged_reason,
        "iterations": iterations,
    }


def populate_extracted_expense(
    extracted_description: str = "Coffee for $2",
    amount: float | None = 2.00,
    category: str | None = "Food",
    date: datetime = datetime.now(timezone.utc),
    confidence_score: float = 0.9,
):
    return ExtractedExpense(
        extracted_description=extracted_description,
        amount=amount,
        category=category,
        date=date,
        confidence_score=confidence_score,
    )
