from app.agent.expense_agent.graph import create_expense_agent_graph
from tests.test_helpers import (
    populate_expense_agent_state,
    populate_extracted_expense,
    setup_mock,
)

graph = create_expense_agent_graph()


class TestExpenseAgent:
    def test_successful_extraction_has_no_flag_attributes(self, mocker, mock_llm):
        """
        Tests successful execution of the expense agent graph as indicated by
        no flags and no flagged_reason in the final output state
        """
        input_state = populate_expense_agent_state()
        setup_mock(populate_extracted_expense(), mocker, mock_llm)

        response = graph.invoke(input_state)

        assert not response["flagged"]
        assert response["flagged_reason"] is None

    def test_successful_extraction_next_attempt_resets_flag_attributes(
        self, mocker, mock_llm
    ):
        """
        Tests that given an unsuccessful attempt of extraction, subsequent successful attempt will reset flag attributes to False ('flagged') and None ('flagged_reason')
        """
        input_state = populate_expense_agent_state()
        mock_structured_llm = mocker.MagicMock()
        mock_structured_llm.invoke.side_effect = [
            populate_extracted_expense(amount=-2),
            populate_extracted_expense(),
        ]
        mock_llm.with_structured_output.return_value = mock_structured_llm

        response = graph.invoke(input_state)

        assert response["iterations"] == 2
        assert not response["flagged"]
        assert response["flagged_reason"] is None

    def test_maximum_attempts_is_three(self, mocker, mock_llm):
        """
        Tests that an invalid description in the input goes through a maximum of 3 runs, resulting in the response having
        'flagged' as True alongside a "flagged_reason"
        """
        input_state = populate_expense_agent_state(
            description="-$2 coffee",
        )
        setup_mock(
            populate_extracted_expense(
                extracted_description="Coffee for -$2", amount=-2.00
            ),
            mocker,
            mock_llm,
        )

        response = graph.invoke(input_state)

        assert response["iterations"] == 3
        assert response["flagged"]
        assert response["flagged_reason"] is not None
