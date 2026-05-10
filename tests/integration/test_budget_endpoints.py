import uuid

from app.schemas.budget_schema import BudgetCreate, BudgetUpdate


class TestGetAllBudget:
    def test_successful_retrieval_from_existing_user(
        self, client, generate_test_budget
    ):
        """
        Tests successful retrieval of a stored budget object tied to an existing user in the db, which is done by retrieving the unique budget id ('id')
        """
        test_user_id = generate_test_budget["user_id"]
        response = client.get(f"/budgets/{test_user_id}")

        assert response.status_code == 200
        assert "id" in response.json()[0]

    def test_retrieve_from_nonexistent_user(self, client):
        """
        Tests that a 404 error is thrown when retrieving budget from a user that is not even registered in the database
        """
        nonexistent_user_id = str(uuid.uuid4())
        response = client.get(f"/budgets/{nonexistent_user_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "User has not set any budgets by category!"

    def test_retrieve_nonexistent_budgets(self, client, generate_test_user):
        """
        Tests that a 404 error is thrown when budgets have yet to be set for a registered user
        """
        test_user_id = generate_test_user["id"]
        response = client.get(f"/budgets/{test_user_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "User has not set any budgets by category!"

    def test_get_with_database_error(self, broken_read_db_client):
        """
        Tests that a 500 error is thrown when a database error occurs during this GET request
        """
        nonexistent_user_id = str(uuid.uuid4())
        response = broken_read_db_client.get(f"/budgets/{nonexistent_user_id}")

        assert response.status_code == 500
        assert response.json()["detail"] == "Database error occurred!"


class TestCreateCategoryBudget:
    def test_successful_creation_for_existing_user(self, client, generate_test_user):
        """
        Tests successful creation of a category budget tied to a user, which is indicated by the presence of the 'id' field which is populated after insertion into the database
        """
        test_user_id = generate_test_user["id"]
        new_category_budget = BudgetCreate(
            category="Transport", month="2026-05", limit=300, user_id=test_user_id
        )
        response = client.post("/budgets/", json=new_category_budget.model_dump())

        assert response.status_code == 200
        assert "id" in response.json()

    def test_create_with_nonexistent_user(self, client):
        """
        Tests that a 404 error is thrown when trying to create a budget for a user that does not exist in the database
        """
        nonexistent_user_id = str(uuid.uuid4())
        new_category_budget = BudgetCreate(
            category="Transport",
            month="2026-05",
            limit=300,
            user_id=nonexistent_user_id,
        )
        response = client.post("/budgets/", json=new_category_budget.model_dump())

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found!"

    def test_create_existing_category_budget(self, client, generate_test_budget):
        """
        Tests that a 409 error is thrown when trying to create a budget that already exists(same month, category pair for a given user_id)
        """
        test_user_id = generate_test_budget["user_id"]
        existing_test_budget = BudgetCreate(
            category="Food", month="2026-05", limit=200, user_id=test_user_id
        )
        response = client.post("/budgets/", json=existing_test_budget.model_dump())

        assert response.status_code == 409
        assert response.json()["detail"] == "Budget for this category already exists!"

    def test_create_with_invalid_month_format(self, client, generate_test_user):
        """
        Tests that a 422 error is thrown when creating a budget with an invalid month format (not %Y-%m)
        """
        test_user_id = generate_test_user["id"]
        response = client.post(
            "/budgets/",
            json={
                "category": "Transport",
                "month": "May 2026",
                "limit": 300,
                "user_id": test_user_id,
            },
        )

        assert response.status_code == 422

    def test_create_with_invalid_limit(self, client, generate_test_user):
        """
        Tests that a 422 error is thrown when creating a budget with an invalid limit value
        """
        test_user_id = generate_test_user["id"]
        response = client.post(
            "/budgets/",
            json={
                "category": "Transport",
                "month": "2026-05",
                "limit": -300,
                "user_id": test_user_id,
            },
        )

        assert response.status_code == 422

    def test_post_with_database_error(self, broken_write_db_client):
        """
        Tests that a 500 error is thrown when a database error occurs during this POST request
        """
        nonexistent_user_id = str(uuid.uuid4())
        new_category_budget = BudgetCreate(
            category="Transport",
            month="2026-05",
            limit=300,
            user_id=nonexistent_user_id,
        )
        response = broken_write_db_client.post(
            "/budgets/", json=new_category_budget.model_dump()
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Database error occurred!"


class TestUpdateCategoryBudget:
    def test_successful_update_for_existing_user(self, client, generate_test_budget):
        """
        Tests successful update of existing category budget for user, which is confirmed by checking whether the 'limit' attribute is updated in the response object
        """
        test_user_id = generate_test_budget["user_id"]
        update_data = BudgetUpdate(category="Food", month="2026-05", limit=300)
        response = client.put(f"/budgets/{test_user_id}", json=update_data.model_dump())

        assert response.status_code == 200
        assert response.json()["limit"] == 300

    def test_update_with_nonexistent_user_id(self, client):
        """
        Tests whether a 404 error is thrown when updating a budget for a user that does not exist in the database
        """
        nonexistent_user_id = str(uuid.uuid4())
        update_data = BudgetUpdate(category="Food", month="2026-05", limit=300)
        response = client.put(
            f"/budgets/{nonexistent_user_id}", json=update_data.model_dump()
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found!"

    def test_update_with_nonexistent_budget(self, client, generate_test_budget):
        """
        Tests whether a 404 error is thrown when updating a nonexistent budget for a registered user
        """
        test_user_id = generate_test_budget["user_id"]
        update_data = BudgetUpdate(category="Transport", month="2026-03", limit=500)
        response = client.put(f"/budgets/{test_user_id}", json=update_data.model_dump())

        assert response.status_code == 404
        assert response.json()["detail"] == "Budget for Transport not set!"

    def test_update_with_invalid_month(self, client, generate_test_budget):
        """
        Tests whether a 422 error is thrown when submitting a payload with an invalid month format (not %Y-%m)
        """
        test_user_id = generate_test_budget["user_id"]
        response = client.put(
            f"/budgets/{test_user_id}",
            json={"category": "Food", "month": "May 2026", "limit": 300},
        )

        assert response.status_code == 422

    def test_update_with_invalid_limit(self, client, generate_test_budget):
        """
        Tests whether a 422 error is thrown when submitting a payload with an invalid limit value
        """
        test_user_id = generate_test_budget["user_id"]
        response = client.put(
            f"/budgets/{test_user_id}",
            json={"category": "Food", "month": "2026-05", "limit": -300},
        )

        assert response.status_code == 422

    def test_put_database_error(self, broken_write_db_client):
        """
        Tests that a 500 error is thrown when a database error occurs during this PUT request
        """
        nonexistent_user_id = str(uuid.uuid4())
        update_data = BudgetUpdate(category="Food", month="2026-05", limit=300)
        response = broken_write_db_client.put(
            f"/budgets/{nonexistent_user_id}", json=update_data.model_dump()
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Database error occurred!"
