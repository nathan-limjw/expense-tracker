import uuid
from datetime import date

from app.schemas.expense_schema import ExpenseCreate, ExpenseUpdate
from tests.test_helpers import populate_extracted_expense, setup_mock


class TestGetExpenseByFilter:
    def test_successful_retrieval_of_all_expenses_no_filter(
        self, client, generate_multiple_expenses
    ):
        """
        Tests successful retrieval of all expenses as shown by the 200 status_code and a list of response objects
        """
        test_user_id = generate_multiple_expenses[0]["expense"]["user_id"]
        response = client.get("/expenses/", params={"user_id": test_user_id})

        assert response.status_code == 200
        assert len(response.json()) > 0

    def test_retrieval_with_nonexistent_user(self, client):
        """
        Tests that a 404 error is thrown when retrieving expenses from a nonexistent user
        """
        nonexistent_user_id = str(uuid.uuid4())

        response = client.get("/expenses/", params={"user_id": nonexistent_user_id})

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found!"

    def test_retrieval_with_nonexistent_expenses(self, client, generate_test_user):
        """
        Tests that a 404 error is thrown when retrieving expenses that are not yet submitted from a registered user
        """
        test_user_id = generate_test_user["id"]
        response = client.get("/expenses/", params={"user_id": test_user_id})

        assert response.status_code == 404
        assert response.json()["detail"] == "No expenses found!"

    def test_filter_by_valid_category(self, client, generate_multiple_expenses):
        """
        Tests successful retrieval of expense objects that are within the specified list of categories
        """
        test_user_id = generate_multiple_expenses[0]["expense"]["user_id"]
        response = client.get(
            "/expenses/", params={"user_id": test_user_id, "category": "Food"}
        )

        assert response.status_code == 200
        assert all(e["category"] == "Food" for e in response.json())

    def test_filter_by_invalid_category(self, client, generate_multiple_expenses):
        """
        Tests that a 422 error is thrown when submitting a category that is invalid and not within the list of specified categories
        """
        test_user_id = generate_multiple_expenses[0]["expense"]["user_id"]
        response = client.get(
            "/expenses/", params={"user_id": test_user_id, "category": "Drinks"}
        )

        assert response.status_code == 422

    def test_filter_by_valid_less_than_amount(self, client, generate_multiple_expenses):
        """
        Tests successful retrieval of expense objects that are valid 'less_than_amount"
        """
        test_user_id = generate_multiple_expenses[0]["expense"]["user_id"]
        response = client.get(
            "/expenses/", params={"user_id": test_user_id, "less_than_amount": 50}
        )

        assert response.status_code == 200
        assert all(e["amount"] <= 50 for e in response.json())

    def test_filter_by_invalid_less_than_amount(
        self, client, generate_multiple_expenses
    ):
        """
        Tests that a 422 error is thrown when retrieving expense objects with an invalid 'less_than_amount'
        """
        test_user_id = generate_multiple_expenses[0]["expense"]["user_id"]
        response = client.get(
            "/expenses/", params={"user_id": test_user_id, "less_than_amount": -50}
        )

        assert response.status_code == 422

    def test_filter_by_valid_date(self, client, generate_multiple_expenses):
        """
        Tests successful retrieval of expense objects with valid "xxx_date" formats in the form "%Y-%m-%d"
        """
        test_user_id = generate_multiple_expenses[0]["expense"]["user_id"]
        response = client.get(
            "/expenses/", params={"user_id": test_user_id, "end_date": "2026-05-12"}
        )

        assert response.status_code == 200
        assert all(
            date.fromisoformat(e["date"][:10]) <= date(2026, 5, 11)
            for e in response.json()
        )

    def test_filter_by_invalid_date(self, client, generate_multiple_expenses):
        """
        Tests that a 422 error is thrown upon retrieval of expense objects with invalid "xxx_date" formats (not in the form "%Y-%m-%d")
        """
        test_user_id = generate_multiple_expenses[0]["expense"]["user_id"]
        response = client.get(
            "/expenses/", params={"user_id": test_user_id, "end_date": "12 May 2026"}
        )

        assert response.status_code == 422

    def test_smaller_start_date_than_end_date(self, client, generate_multiple_expenses):
        """
        Tests that a 422 error is thrown upon retrieval of expense objects when start_date is larger than end_date
        """
        test_user_id = generate_multiple_expenses[0]["expense"]["user_id"]
        response = client.get(
            "/expenses/",
            params={
                "user_id": test_user_id,
                "start_date": "2026-05-12",
                "end_date": "2026-05-11",
            },
        )

        assert response.status_code == 422
        assert response.json()["detail"] == "start_date cannot be after end_date"


class TestGetExpenseWithID:
    def test_successful_retrieval_of_expense(self, client, generate_test_expense):
        """
        Tests successful retrieval of expense with a registered user
        """
        test_expense_id = generate_test_expense["expense"]["id"]
        response = client.get(f"/expenses/{test_expense_id}")

        assert response.status_code == 200

    def test_retrieval_of_nonexistent_expense(self, client):
        """
        Tests that a 404 error will be thrown when querying a expense id that is not registered in the db
        """
        nonexistent_expense_id = str(uuid.uuid4())
        response = client.get(f"/expenses/{nonexistent_expense_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Expense not found!"

    def test_get_with_database_error(self, broken_read_db_client):
        """
        Tests that a 500 error will be thrown when a database error occurs during this GET request
        """
        nonexistent_expense_id = str(uuid.uuid4())
        response = broken_read_db_client.get(f"/expenses/{nonexistent_expense_id}")

        assert response.status_code == 500
        assert response.json()["detail"] == "Database error occurred!"


class TestCreateExpense:
    def test_successful_creation_of_expense(
        self, client, generate_test_user, mocker, mock_llm
    ):
        """
        Tests successful creation of an expense with a registered user, which is indicated by a unique UUID value ('id') that is populated after successful addition of the expense into the database
        """
        test_user_id = generate_test_user["id"]
        setup_mock(populate_extracted_expense(), mocker, mock_llm)

        test_expense = ExpenseCreate(
            description="Coffee for $2 after lunch today", user_id=test_user_id
        )

        response = client.post("/expenses/", json=test_expense.model_dump())

        assert response.status_code == 200
        assert "id" in response.json()["expense"]

    def test_creation_with_nonexistent_user(self, client):
        """
        Tests that a 404 error will be thrown when creating an expense and tying it to a user that is not registered to the database
        """
        nonexistent_user_id = str(uuid.uuid4())

        test_expense = ExpenseCreate(
            description="Coffee for $2 after lunch today", user_id=nonexistent_user_id
        )

        response = client.post("/expenses/", json=test_expense.model_dump())

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found, create a user first!"

    def test_graph_value_error(self, client, generate_test_user, mock_agent):
        """
        Tests that a 400 error is thrown when a ValueError occurs
        """
        test_user_id = generate_test_user["id"]

        mock_agent.invoke.side_effect = ValueError("Invalid input!")

        test_expense = ExpenseCreate(
            description="Coffee for $2 after lunch today", user_id=test_user_id
        )

        response = client.post("/expenses/", json=test_expense.model_dump())

        assert response.status_code == 400

    def test_graph_runtime_error(self, client, generate_test_user, mock_agent):
        """
        Tests that a 500 error is thrown when a RuntimeError occurs
        """
        test_user_id = generate_test_user["id"]

        mock_agent.invoke.side_effect = RuntimeError("Runtime error occurred!")

        test_expense = ExpenseCreate(
            description="Coffee for $2 after lunch today", user_id=test_user_id
        )

        response = client.post("/expenses/", json=test_expense.model_dump())

        assert response.status_code == 500

    def test_graph_unexpected_error(self, client, generate_test_user, mock_agent):
        """
        Tests that a 500 error is thrown when any unexpected error occurs
        """
        test_user_id = generate_test_user["id"]

        mock_agent.invoke.side_effect = Exception("Unexpected error occurred!")

        test_expense = ExpenseCreate(
            description="Coffee for $2 after lunch today", user_id=test_user_id
        )

        response = client.post("/expenses/", json=test_expense.model_dump())

        assert response.status_code == 500

    def test_creation_with_flagged_state(
        self, client, generate_test_user, mock_agent, mocker
    ):
        """
        Tests that a 422 error is thrown when 'flagged' is set to True in the state during the course of traversing through the graph
        """
        test_user_id = generate_test_user["id"]

        mock_agent.invoke.return_value = {
            "extracted_info": mocker.MagicMock(),
            "flagged": True,
            "flagged_reason": "Could not extract a valid amount. Please include a valid and proper amount for extraction.",
        }

        test_expense = ExpenseCreate(
            description="Coffee for -$2 after lunch today", user_id=test_user_id
        )

        response = client.post("/expenses/", json=test_expense.model_dump())

        assert response.status_code == 422
        assert (
            response.json()["detail"]
            == "Could not extract a valid amount. Please include a valid and proper amount for extraction."
        )

    def test_creation_with_empty_extraction_info(
        self, client, generate_test_user, mock_agent, mocker
    ):
        """
        Tests that a 500 error is thrown when 'extracted_info' is None in the state during the course of traversing through the graph
        """
        test_user_id = generate_test_user["id"]

        mock_agent.invoke.return_value = {"extracted_info": None}

        test_expense = ExpenseCreate(
            description="INVALID USER DESCRIPTION", user_id=test_user_id
        )
        response = client.post("/expenses/", json=test_expense.model_dump())

        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to extract expense information"

    def test_post_with_database_error(self, broken_write_db_client, mocker, mock_agent):
        """
        Tests that a 500 error will be thrown when a database error occurs during this POST request
        """
        mock_agent.invoke.return_value = {
            "extracted_info": mocker.MagicMock(),
            "flagged": False,
            "flagged_reason": None,
        }
        nonexistent_user_id = str(uuid.uuid4())

        test_expense = ExpenseCreate(
            description="Coffee for $2 after lunch today", user_id=nonexistent_user_id
        )

        response = broken_write_db_client.post(
            "/expenses/", json=test_expense.model_dump()
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Database error occurred!"


class TestUpdateExpense:
    def test_successful_update_of_expense(self, client, generate_test_expense):
        """
        Tests successful update of expense as indicated by the updated "amount" in the response object
        """
        test_expense_id = generate_test_expense["expense"]["id"]

        update_data = ExpenseUpdate(amount=500, category="Food")
        response = client.put(
            f"/expenses/{test_expense_id}", json=update_data.model_dump()
        )

        assert response.status_code == 200
        assert response.json()["amount"] == 500

    def test_update_of_nonexistent_expense(self, client):
        """
        Tests that a 404 error will be thrown when updating an expense that does not exist in the database
        """
        nonexistent_expense_id = str(uuid.uuid4())

        update_data = ExpenseUpdate(amount=500, category="Food")
        response = client.put(
            f"/expenses/{nonexistent_expense_id}", json=update_data.model_dump()
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Expense not found!"

    def test_update_with_invalid_category(self, client, generate_test_expense):
        """
        Tests that a 422 error will be thrown when an invalid category is input into the payload for the endpoint
        """
        test_expense_id = generate_test_expense["expense"]["id"]

        response = client.put(
            f"/expenses/{test_expense_id}", json={"amount": 500, "category": "Drinks"}
        )

        assert response.status_code == 422

    def test_update_with_invalid_amount(self, client, generate_test_expense):
        """
        Tests that a 422 error will be thrown when an invalid amount is input into the payload for the endpoint
        """
        test_expense_id = generate_test_expense["expense"]["id"]

        response = client.put(
            f"/expenses/{test_expense_id}", json={"amount": -2.0, "category": "Food"}
        )

        assert response.status_code == 422

    def test_put_with_database_error(self, broken_write_db_client):
        """
        Tests that a 500 error will be thrown when a database error occurs during this PUT request
        """
        nonexistent_expense_id = str(uuid.uuid4())

        update_data = ExpenseUpdate(amount=500, category="Food")
        response = broken_write_db_client.put(
            f"/expenses/{nonexistent_expense_id}", json=update_data.model_dump()
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Database error occurred!"


class TestDeleteExpense:
    def test_successful_deletion_of_expense(self, client, generate_test_expense):
        """
        Tests successful deletion of an existent expense as indicated by a 404 error being thrown after querying for the same expense ID after deletion
        """
        test_expense_id = generate_test_expense["expense"]["id"]

        response = client.delete(f"/expenses/{test_expense_id}")

        assert response.status_code == 200

        query_expense_by_id = client.get(f"/expenses/{test_expense_id}")

        assert query_expense_by_id.status_code == 404
        assert query_expense_by_id.json()["detail"] == "Expense not found!"

    def test_deletion_of_nonexistent_expense(self, client):
        """
        Tests that a 404 error is thrown when deleting an expense that is not registered into the database
        """
        nonexistent_expense_id = str(uuid.uuid4())
        response = client.delete(f"/expenses/{nonexistent_expense_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "Expense not found!"

    def test_delete_with_database_error(self, broken_read_db_client):
        """
        Tests that a 500 error will be thrown when a database error occurs during this DELETE request
        """
        nonexistent_expense_id = str(uuid.uuid4())
        response = broken_read_db_client.delete(f"/expenses/{nonexistent_expense_id}")

        assert response.status_code == 500
        assert response.json()["detail"] == "Database error occurred!"
