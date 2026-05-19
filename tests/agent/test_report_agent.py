from app.agent.report_agent.graph import create_report_agent_graph

graph = create_report_agent_graph()


class TestReportAgentGraph:
    def test_success_graph_returns_final_report(
        self, mock_s3, mock_report_llm, db_session, report_input
    ):
        mock_report_llm.invoke.return_value.content = "Some financial advice"

        result = graph.invoke(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert "final_report" in result

    def test_both_analyst_and_visualiser_nodes_ran(
        self, db_session, mock_report_llm, mock_s3, report_input
    ):
        mock_report_llm.invoke.return_value.content = "Some financial advice"

        result = graph.invoke(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert result["financial_advice"] == "Some financial advice"
        assert isinstance(result["chart_image_bytes"]["pie"], bytes)
        assert isinstance(result["chart_image_bytes"]["bar"], bytes)

    def test_presenter_receives_output_from_both_branches(
        self, db_session, mock_report_llm, mock_s3, report_input
    ):
        mock_report_llm.invoke.return_value.content = "Some financial advice"

        result = graph.invoke(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert result["final_report"]["summary"] == "Some financial advice"
        assert result["final_report"]["charts"]["pie"].startswith("https://")
        assert result["final_report"]["charts"]["bar"].startswith("https://")

    def test_graph_with_no_expenses_still_completes(
        self, db_session, report_input, mock_report_llm, mock_s3
    ):
        mock_report_llm.invoke.return_value.content = "Some financial advice"

        result = graph.invoke(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert result["final_report"]["total_spent"] == 0.0
        assert result["final_report"]["categories"] == []
