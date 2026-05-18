import pytest

from app.agent.expense_agent.nodes import (
    decision_node,
    extraction_node,
    validation_node,
)
from tests.test_helpers import (
    populate_expense_agent_state,
    populate_extracted_expense,
    setup_mock,
)
from utils.config import settings

## Helper Functions


class TestExtractionNode:
    def test_first_attempt_uses_extraction_prompt(self, mocker, mock_expense_llm):
        """
        Tests that during the first attempt, the correct prompt is used: the extraction prompt does not contain the 'flagged_reason' attribute
        """
        extracted_output = populate_extracted_expense()

        mock_structured_llm = mocker.MagicMock()
        mock_structured_llm.invoke.return_value = extracted_output

        mock_expense_llm.with_structured_output.return_value = mock_structured_llm

        extraction_node(populate_expense_agent_state())

        messages = mock_structured_llm.invoke.call_args[0][0]
        system_message = messages[0].content

        assert "flagged_reason" not in system_message

    def test_retry_attempt_uses_retry_extraction_prompt(self, mocker, mock_expense_llm):
        """
        Tests that on subsequent attempts, the retry extraction prompt is used: contains the exact value of
        'flagged_reason' inside the prompt
        """
        extracted_output = populate_extracted_expense()

        mock_structured_llm = mocker.MagicMock()
        mock_structured_llm.invoke.return_value = extracted_output

        mock_expense_llm.with_structured_output.return_value = mock_structured_llm

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

    def test_incrementation_of_iteration(self, mocker, mock_expense_llm):
        """
        Checks if the 'iterations' attribute in the state is incremented by 1 after completion of extraction

        """
        extracted_output = populate_extracted_expense()

        setup_mock(extracted_output, mocker, mock_expense_llm)

        result = extraction_node(populate_expense_agent_state())

        assert result["iterations"] == 1

    def test_retry_resets_flagged_attributes(self, mocker, mock_expense_llm):
        """
        Checks that on retry attempts, the 'flagged' attribute is reset to False (originally True) and 'flagged_reason' is set to None (originally containing a string)
        """
        extracted_output = populate_extracted_expense()

        setup_mock(extracted_output, mocker, mock_expense_llm)

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
        """
        Checks if the validation node correctly flags the input when no information could be extracted,
        returning the appropriate 'flagged_reason' message
        """
        input_state = {"extracted_info": None}
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Unable to extract information. Please rephrase your input."
        )

    def test_null_amount(self):
        """
        Tests that the validation node correctly flags the input when the amount is null, returning the appropriate 'flagged_reason' message
        """
        input_state = {"extracted_info": populate_extracted_expense(amount=None)}
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Could not extract a valid amount. Please include a valid and proper amount for extraction."
        )

    def test_zero_amount(self):
        """
        Tests that the validation node correctly flags the input when the amount is zero, returning the appropriate 'flagged_reason' message
        """
        input_state = {"extracted_info": populate_extracted_expense(amount=0)}
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Could not extract a valid amount. Please include a valid and proper amount for extraction."
        )

    def test_negative_amount(self):
        """
        Tests that the validation node correctly flags the input when the amount is negative, returning the appropriate 'flagged_reason' message
        """
        input_state = {"extracted_info": populate_extracted_expense(amount=-2)}
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Could not extract a valid amount. Please include a valid and proper amount for extraction."
        )

    def test_null_category(self):
        """
        Tests that the validation node correctly flags the input when the category is null, returning the appropriate 'flagged_reason' message
        """
        input_state = {"extracted_info": populate_extracted_expense(category=None)}
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Could not determine a category. Be more specific."
        )

    def test_low_confidence_score(self):
        """
        Tests that the validation node correctly flags the input when the confidence score is below the defined threshold, returning the appropriate 'flagged_reason' message
        """
        input_state = {
            "extracted_info": populate_extracted_expense(
                confidence_score=(0.5 * settings.CONFIDENCE_THRESHOLD)
            )
        }
        result = validation_node(input_state)

        assert result["flagged"]
        assert (
            result["flagged_reason"]
            == "Input was unclear. Please rephrase and try again."
        )

    def test_boundary_confidence_score(self):
        """
        Tests that the validation node does not flag the input when the confidence score is exactly equal to the defined threshold
        """
        input_state = {
            "extracted_info": populate_extracted_expense(
                confidence_score=settings.CONFIDENCE_THRESHOLD
            )
        }
        result = validation_node(input_state)

        assert not result["flagged"]
        assert result["flagged_reason"] is None

    def test_successful_validation(self):
        """
        Tests that the validation node does not flag the input when all extracted information is valid and the confidence score is above the defined threshold"""
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
        """
        Tests the decision node's routing logic based on different combinations of 'flagged' status and 'iterations' count, ensuring that it correctly routes to 'END' or back to 'extraction' as per the defined conditions
        """
        input_state = {"flagged": flag, "iterations": iteration}

        result = decision_node(input_state)
        assert result == route
