import uuid

from app.schemas.report_schema import ReportCreate


class TestGetReport:
    def test_successful_report_generation(
        self, client, generate_test_user, mock_report_agent
    ):
        mock_report_agent.invoke.return_value = {
            "month": "2026-05",
            "total_spent": 164.60,
            "monthly_budget": 1000,
            "days_in_period": 31,
            "current_day": 18,
            "categories": [
                {
                    "category": "Food",
                    "spent": 8.0,
                    "budget": 200.0,
                    "variance": -192.0,
                    "variance_pct": 4.0,
                },
                {
                    "category": "Transport",
                    "spent": 81.0,
                    "budget": None,
                    "variance": None,
                    "variance_pct": None,
                },
            ],
            "summary": "Some financial advice",
            "charts": {
                "pie": "https://s3.amazonaws.com/pie.png",
                "bar": "https://s3.amazonaws.com/bar.png",
            },
        }

        payload = ReportCreate(user_id=generate_test_user["id"], month="2026-05")
        response = client.post("/report/", json=payload.model_dump())

        assert response.status_code == 200

    def test_user_not_found(self, client):
        nonexistent_user_id = str(uuid.uuid4())
        payload = ReportCreate(user_id=nonexistent_user_id, month="2026-05")

        response = client.post("/report/", json=payload.model_dump())

        assert response.status_code == 404

    def test_graph_value_error(self, client, generate_test_user, mock_report_agent):
        mock_report_agent.invoke.side_effect = ValueError("Invalid input!")

        payload = ReportCreate(user_id=generate_test_user["id"], month="2026-05")
        response = client.post("/report/", json=payload.model_dump())

        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid input!"

    def test_runtime_value_error(self, client, generate_test_user, mock_report_agent):
        mock_report_agent.invoke.side_effect = RuntimeError("Runtime error occurred!")

        payload = ReportCreate(user_id=generate_test_user["id"], month="2026-05")
        response = client.post("/report/", json=payload.model_dump())

        assert response.status_code == 500
        assert response.json()["detail"] == "Runtime error occurred!"

    def test_unexpected_value_error(
        self, client, generate_test_user, mock_report_agent
    ):
        mock_report_agent.invoke.side_effect = Exception()

        payload = ReportCreate(user_id=generate_test_user["id"], month="2026-05")
        response = client.post("/report/", json=payload.model_dump())

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to generate report"

    def test_post_with_broken_database(self, broken_read_db_client):
        nonexistent_user_id = str(uuid.uuid4())
        payload = ReportCreate(user_id=nonexistent_user_id, month="2026-05")

        response = broken_read_db_client.post("/report/", json=payload.model_dump())

        assert response.status_code == 500
        assert response.json()["detail"] == "Database error occurred!"
