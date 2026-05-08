import pytest


@pytest.fixture
def mock_llm(mocker):
    return mocker.patch("app.agent.expense_agent.nodes.llm")
