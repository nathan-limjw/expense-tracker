from app.agent.expense_agent.schemas import ExtractedExpense


def setup_mock(extracted_expense: ExtractedExpense, mocker, mock_llm):
    extracted_output = extracted_expense

    mock_structured_llm = mocker.MagicMock()
    mock_structured_llm.invoke.return_value = extracted_output

    mock_llm.with_structured_output.return_value = mock_structured_llm
