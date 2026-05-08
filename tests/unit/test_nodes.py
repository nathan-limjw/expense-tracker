from datetime import datetime, timezone

import pytest

from app.agent.expense_agent.nodes import (
    decision_node,
    extraction_node,
    validation_node,
)
from app.agent.expense_agent.schemas import ExtractedExpense
from app.schemas.expense_schema import ExpenseCreate
from utils.config import CONFIDENCE_THRESHOLD
from utils.test_helpers import setup_mock

## Helper Functions


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


class TestExtractionNode:
    def test_first_attempt_uses_extraction_prompt(self, mocker, mock_llm):
        extracted_output = populate_extracted_expense()

        mock_structured_llm = mocker.MagicMock()
        mock_structured_llm.invoke.return_value = extracted_output

        mock_llm.with_structured_output.return_value = mock_structured_llm

        extraction_node(populate_expense_agent_state())

        messages = mock_structured_llm.invoke.call_args[0][0]
        system_message = messages[0].content

        assert "flagged_reason" not in system_message

    def test_retry_attempt_uses_retry_extraction_prompt(self, mocker, mock_llm):
        extracted_output = populate_extracted_expense()

        mock_structured_llm = mocker.MagicMock()
        mock_structured_llm.invoke.return_value = extracted_output

        mock_llm.with_structured_output.return_value = mock_structured_llm

        extraction_node(
            populate_expense_agent_state(
                iterations=1,
                flagged=True,
                flagged_reason="Could not determine a category. Be more specific.",
            )
        )

        messages = mock_structured_llm.invoke.call_args[0][0]
        system_message = messages[0].content

        assert "Could not determine a category. Be more specific." in system_message

    def test_incrementation_of_iteration(self, mocker, mock_llm):
        extracted_output = populate_extracted_expense()

        setup_mock(extracted_output, mocker, mock_llm)

        result = extraction_node(populate_expense_agent_state())

        assert result["iterations"] == 1

    def test_retry_resets_flagged_attributes(self, mocker, mock_llm):
        extracted_output = populate_extracted_expense()

        setup_mock(extracted_output, mocker, mock_llm)

        result = extraction_node(
            populate_expense_agent_state(
                iterations=1,
                flagged=True,
                flagged_reason="Could not determine a category. Be more specific.",
            )
        )

        assert not result["flagged"]
        assert result["flagged_reason"] is None


class TestValidationNode:
    def test_empty_extraction_info(self):
        input_state = {"extracted_info": None}
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Unable to extract information. Please rephrase your input."
        )

    def test_null_amount(self):
        input_state = {"extracted_info": populate_extracted_expense(amount=None)}
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Could not extract a valid amount. Please include a valid and proper amount for extraction."
        )

    def test_zero_amount(self):
        input_state = {"extracted_info": populate_extracted_expense(amount=0)}
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Could not extract a valid amount. Please include a valid and proper amount for extraction."
        )

    def test_negative_amount(self):
        input_state = {"extracted_info": populate_extracted_expense(amount=-2)}
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Could not extract a valid amount. Please include a valid and proper amount for extraction."
        )

    def test_null_category(self):
        input_state = {"extracted_info": populate_extracted_expense(category=None)}
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Could not determine a category. Be more specific."
        )

    def test_low_confidence_score(self):
        input_state = {
            "extracted_info": populate_extracted_expense(
                confidence_score=(0.5 * CONFIDENCE_THRESHOLD)
            )
        }
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Input was unclear. Please rephrase and try again."
        )

    def test_boundary_confidence_score(self):
        input_state = {
            "extracted_info": populate_extracted_expense(
                confidence_score=CONFIDENCE_THRESHOLD
            )
        }
        result = validation_node(input_state)

        assert not result["flagged"]
        assert result["flagged_reason"] is None

    def test_successful_validation(self):
        input_state = {"extracted_info": populate_extracted_expense()}
        result = validation_node(input_state)

        assert not result["flagged"]
        assert result["flagged_reason"] is None


class TestDecisionNode:
    @pytest.mark.parametrize(
        "flag, iteration, route",
        [
            (False, 1, "END"),
            (True, 2, "extraction"),
            (True, 3, "END"),
            (True, 1, "extraction"),
        ],
        ids=[
            "successful_extraction",
            "boundary_iteration",
            "exceed_max_extraction_attempts",
            "failed_extraction_below_max_extraction_attempts",
        ],
    )
    def test_decision_node(self, flag, iteration, route):
        input_state = {"flagged": flag, "iterations": iteration}

        result = decision_node(input_state)
        assert result == route
