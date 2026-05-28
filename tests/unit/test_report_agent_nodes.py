import base64
from datetime import date

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.report_agent.nodes.accountant_node import accountant_node
from app.agent.report_agent.nodes.analyst_node import _build_human_message, analyst_node
from app.agent.report_agent.nodes.presenter_node import presenter_node
from app.agent.report_agent.nodes.visualiser_node import visualiser_node
from app.agent.report_agent.prompts import ANALYST_SYSTEM_PROMPT
from app.models.budget import Budget
from app.models.expense import Expense
from app.models.user import User
from app.schemas.report_schema import ReportCreate


class TestAccountantNode:
    def test_success_returns_raw_data_key(self, db_session, report_input):
        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert "raw_data" in result

    def test_total_spent_sums_expenses_for_month(
        self, db_session, test_user, report_input
    ):
        db_session.add_all(
            [
                Expense(
                    user_id=test_user.id,
                    category="Food",
                    amount=13.0,
                    date=date(2026, 4, 27),
                    description="McDelivery for $13",
                ),
                Expense(
                    user_id=test_user.id,
                    category="Food",
                    amount=20.0,
                    date=date(2026, 5, 1),
                    description="Pad Thai for $20",
                ),
                Expense(
                    user_id=test_user.id,
                    category="Food",
                    amount=30.0,
                    date=date(2026, 5, 10),
                    description="Cafe Lunch Set for $30",
                ),
            ]
        )
        db_session.commit()

        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert result["raw_data"]["total_spent"] == 50.0

    def test_expenses_from_other_users_excluded(
        self, db_session, test_user, report_input
    ):
        other_user = User(name="other", email="other@gmail.com", monthly_budget=500)

        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        db_session.add_all(
            [
                Expense(
                    user_id=test_user.id,
                    category="Food",
                    amount=20.0,
                    date=date(2026, 5, 1),
                    description="Pad Thai for $20",
                ),
                Expense(
                    user_id=other_user.id,
                    category="Food",
                    amount=30.0,
                    date=date(2026, 5, 10),
                    description="Cafe Lunch Set for $30",
                ),
            ]
        )
        db_session.commit()

        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert result["raw_data"]["total_spent"] == 20.0

    def test_no_expenses_returns_zero_total(self, report_input, db_session):
        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert result["raw_data"]["total_spent"] == 0.0

    def test_monthly_budget_returned_from_user(self, report_input, db_session):
        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert result["raw_data"]["monthly_budget"] == 1000.0

    def test_monthly_budget_is_none_when_not_set(self, db_session):
        other_user = User(name="other", email="other@gmail.com")
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        report_input = ReportCreate(user_id=other_user.id, month="2026-05")

        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert not result["raw_data"]["monthly_budget"]

    def test_categories_grouped_correctly(self, db_session, test_user, report_input):
        db_session.add_all(
            [
                Expense(
                    user_id=test_user.id,
                    category="Food",
                    amount=20.0,
                    date=date(2026, 5, 1),
                    description="Pad Thai for $20",
                ),
                Expense(
                    user_id=test_user.id,
                    category="Food",
                    amount=6.0,
                    date=date(2026, 5, 5),
                    description="Iced Matcha Latte for $6",
                ),
                Expense(
                    user_id=test_user.id,
                    category="Shopping",
                    amount=25.0,
                    date=date(2026, 5, 10),
                    description="Thrifted Jorts for $25",
                ),
                Expense(
                    user_id=test_user.id,
                    category="Utilities",
                    amount=7.77,
                    date=date(2026, 5, 1),
                    description="Phone Bill for $7.77",
                ),
            ]
        )

        db_session.commit()

        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        categories = {
            c["category"]: c["spent"] for c in result["raw_data"]["categories"]
        }

        assert categories["Shopping"] == 25.0
        assert categories["Utilities"] == 7.77
        assert categories["Food"] == 26.0

    def test_variance_computed_when_category_budget_set(
        self, db_session, test_user, report_input
    ):
        db_session.add(
            Expense(
                user_id=test_user.id,
                category="Food",
                amount=20.0,
                date=date(2026, 5, 1),
                description="Pad Thai for $20",
            )
        )
        db_session.add(
            Budget(user_id=test_user.id, category="Food", month="2026-05", limit=200.0)
        )
        db_session.commit()

        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )
        food = next(
            c for c in result["raw_data"]["categories"] if c["category"] == "Food"
        )
        assert food["budget"] == 200.0
        assert food["variance"] == round(20.0 - 200.0, 2)
        assert food["variance_pct"] == round((20.0 / 200.0) * 100, 1)

    def test_variance_is_none_when_category_budget_not_set(
        self, db_session, test_user, report_input
    ):
        db_session.add(
            Expense(
                user_id=test_user.id,
                category="Food",
                amount=20.0,
                date=date(2026, 5, 1),
                description="Pad Thai for $20",
            )
        )

        db_session.commit()

        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        food = next(
            c for c in result["raw_data"]["categories"] if c["category"] == "Food"
        )

        assert not food["budget"]
        assert not food["variance"]
        assert not food["variance_pct"]

    def test_category_budget_from_other_month_not_applied(
        self, db_session, test_user, report_input
    ):
        db_session.add(
            Expense(
                user_id=test_user.id,
                category="Food",
                amount=20.0,
                date=date(2026, 5, 1),
                description="Pad Thai for $20",
            )
        )
        db_session.add(
            Budget(user_id=test_user.id, category="Food", month="2026-04", limit=100.0)
        )

        db_session.commit()

        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        food = next(
            c for c in result["raw_data"]["categories"] if c["category"] == "Food"
        )

        assert not food["budget"]
        assert not food["variance"]
        assert not food["variance_pct"]

    def test_days_in_period_correct_for_may(self, db_session, report_input):
        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert result["raw_data"]["days_in_period"] == 31

    def test_historical_month_current_day_equals_days_in_period(
        self, db_session, test_user
    ):
        report_input = ReportCreate(user_id=test_user.id, month="2025-01")
        result = accountant_node(
            {"input": report_input}, {"configurable": {"db": db_session}}
        )

        assert result["raw_data"]["current_day"] == result["raw_data"]["days_in_period"]


class TestAnalystNode:
    def test_returns_financial_advice(self, mock_full_state, mock_report_llm):
        mock_report_llm.invoke.return_value.content = "INSERT FINANCIAL ADVICE"

        result = analyst_node(mock_full_state)

        assert result["financial_advice"] == "INSERT FINANCIAL ADVICE"

    def test_llm_called_with_system_and_human_messages(
        self, mock_full_state, mock_report_llm
    ):
        mock_report_llm.invoke.return_value.content = "INSERT FINANCIAL ADVICE"

        analyst_node(mock_full_state)

        messages = mock_report_llm.invoke.call_args[0][0]

        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], HumanMessage)
        assert ANALYST_SYSTEM_PROMPT in messages[0].content
        assert "2026-05" in messages[1].content

    def test_llm_exception_propagates(self, mock_full_state, mock_report_llm):
        mock_report_llm.invoke.side_effect = RuntimeError("LLM is down")

        with pytest.raises(RuntimeError, match="LLM is down"):
            analyst_node(mock_full_state)


class TestBuildHumanMessage:
    def test_contains_month(self, mock_raw_data):
        msg = _build_human_message(mock_raw_data, "2026-05")

        assert "2026-05" in msg

    def test_contains_total_spent(self, mock_raw_data):
        msg = _build_human_message(mock_raw_data, "2026-05")

        assert "164.60" in msg

    def test_contains_category_names(self, mock_raw_data):
        msg = _build_human_message(mock_raw_data, "2026-05")

        assert "Food" in msg
        assert "Transport" in msg

    def test_human_message_shows_percentage_when_budget_set(self, mock_raw_data):
        msg = _build_human_message(mock_raw_data, "2026-05")

        assert "16.5%" in msg

    def test_human_message_shows_no_budget_when_monthly_budget_is_none(
        self, mock_raw_data
    ):
        mock_raw_data["monthly_budget"] = None

        msg = _build_human_message(mock_raw_data, "2026-05")

        assert "No overall budget set" in msg

    def test_shows_na_when_category_has_no_budget(self, mock_raw_data):
        msg = _build_human_message(mock_raw_data, "2026-05")

        assert "N/A" in msg  # Transport has no budget


class TestVisualiserNode:
    def test_success_returns_pie_and_bar_keys(self, mock_full_state):
        result = visualiser_node(mock_full_state)

        assert "chart_image_bytes" in result
        assert "pie" in result["chart_image_bytes"]
        assert "bar" in result["chart_image_bytes"]

    def test_outputs_are_bytes(self, mock_full_state):
        result = visualiser_node(mock_full_state)

        assert isinstance(result["chart_image_bytes"]["pie"], bytes)
        assert isinstance(result["chart_image_bytes"]["bar"], bytes)

    def test_handles_empty_categories(self, mock_full_state):
        mock_full_state["raw_data"]["categories"] = []
        result = visualiser_node(mock_full_state)

        assert isinstance(result["chart_image_bytes"]["pie"], bytes)
        assert isinstance(result["chart_image_bytes"]["bar"], bytes)

    def test_handles_categories_with_no_budget(self, mock_full_state):
        # Transport in mock_raw_data has budget=None — ensure no crash
        mock_full_state["raw_data"]["categories"][1]["budget"] = None
        result = visualiser_node(mock_full_state)

        assert "chart_image_bytes" in result

    def test_outputs_are_valid_png(self, mock_full_state):
        PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
        result = visualiser_node(mock_full_state)

        assert result["chart_image_bytes"]["pie"][:8] == PNG_SIGNATURE
        assert result["chart_image_bytes"]["bar"][:8] == PNG_SIGNATURE


class TestPresenterNode:
    def test_success_returns_final_report_and_associated_fields(
        self, mock_full_state, mock_s3
    ):
        result = presenter_node(mock_full_state)

        assert "final_report" in result

        final_report = result["final_report"]

        assert final_report["month"] == mock_full_state["input"].month
        assert final_report["total_spent"] == mock_full_state["raw_data"]["total_spent"]
        assert (
            final_report["monthly_budget"]
            == mock_full_state["raw_data"]["monthly_budget"]
        )
        assert (
            final_report["days_in_period"]
            == mock_full_state["raw_data"]["days_in_period"]
        )
        assert final_report["current_day"] == mock_full_state["raw_data"]["current_day"]

        assert final_report["categories"] == mock_full_state["raw_data"]["categories"]

        assert final_report["summary"] == mock_full_state["financial_advice"]

    def test_chart_bytes_are_base64_encoded(self, mock_full_state, mock_s3):
        result = presenter_node(mock_full_state)

        pie = result["final_report"]["chart_bytes"]["pie"]
        bar = result["final_report"]["chart_bytes"]["bar"]

        assert pie == base64.b64encode(b"fakepie").decode("utf-8")
        assert bar == base64.b64encode(b"fakebar").decode("utf-8")

    def test_s3_upload_called_twice(self, mock_full_state, mock_s3):
        presenter_node(mock_full_state)

        assert mock_s3.put_object.call_count == 2

    def test_s3_upload_uses_correct_keys(self, mock_full_state, mock_s3):
        user_id = mock_full_state["input"].user_id
        month = mock_full_state["input"].month

        presenter_node(mock_full_state)

        called_keys = {call.kwargs["Key"] for call in mock_s3.put_object.call_args_list}

        assert f"reports/{user_id}/{month}/pie.png" in called_keys
        assert f"reports/{user_id}/{month}/bar.png" in called_keys

    def test_chart_urls_are_valid_s3_urls(self, mock_full_state, mock_s3):
        user_id = mock_full_state["input"].user_id
        month = mock_full_state["input"].month

        result = presenter_node(mock_full_state)
        pie_url = result["final_report"]["charts"]["pie"]
        bar_url = result["final_report"]["charts"]["bar"]

        assert pie_url.startswith("https://")
        assert f"{user_id}/{month}/pie.png" in pie_url
        assert bar_url.startswith("https://")
        assert f"{user_id}/{month}/bar.png" in bar_url

    def test_s3_exception_propagates(self, mock_full_state, mock_s3):
        mock_s3.put_object.side_effect = Exception("S3 unavailable")

        with pytest.raises(Exception, match="S3 unavailable"):
            presenter_node(mock_full_state)
