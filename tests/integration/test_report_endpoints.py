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
