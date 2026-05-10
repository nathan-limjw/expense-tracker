import uuid

from app.schemas.user_schema import UserCreate, UserUpdate


class TestGetUserByID:
    def test_user_id_in_database(self, client, generate_test_user):
        """
        Tests that a user can be retrieved by their ID and their respective data is returned
        """
        test_user_id = generate_test_user["id"]
        response = client.get(f"/users/{test_user_id}")

        assert response.status_code == 200
        assert response.json()["name"] == "kimmy"
        assert response.json()["email"] == "kimmy@gmail.com"
        assert response.json()["monthly_budget"] == 1000

    def test_user_id_not_in_database(self, client):
        """
        Tests that a 404 error is thrown whenever a nonexistent user ID is queried
        """
        nonexistent_user_id = str(uuid.uuid4())
        response = client.get(f"/users/{nonexistent_user_id}")

        assert response.status_code == 404
        assert response.json()["detail"] == "User not found!"

    def test_get_with_database_error(self, broken_read_db_client):
        """
        Tests that a 500 error is thrown whenever a database error occurs during this GET request
        """
        nonexistent_user_id = str(uuid.uuid4())
        response = broken_read_db_client.get(f"/users/{nonexistent_user_id}")

        assert response.status_code == 500
        assert response.json()["detail"] == "Database error occurred!"


class TestCreateUser:
    def test_create_first_time_user(self, client):
        """
        Tests that a user can be created with valid credentials, as indicated by the populated fields in the return object
        """
        test_new_user = UserCreate(
            name="test123", email="test123@gmail.com", monthly_budget=200
        )
        response = client.post("/users/", json=test_new_user.model_dump())

        assert response.status_code == 200
        assert "id" in response.json()
        assert "created_at" in response.json()
        assert "updated_at" in response.json()

    def test_create_already_existing_user(self, client, generate_test_user):
        """
        Tests than a 409 error is thrown when an email that is existent in the database is used to create another user (email is unique to every user)
        """
        test_user = UserCreate(
            name="kimmy", email="kimmy@gmail.com", monthly_budget=1000
        )
        response = client.post("/users/", json=test_user.model_dump())

        assert response.status_code == 409
        assert response.json()["detail"] == "User already registered!"

    def test_create_invalid_email(self, client):
        """
        Tests that a 422 error is thrown when an invalid email is used to create a user
        """
        response = client.post(
            "/users/",
            json={"name": "kimmy", "email": "kimmynotemail", "monthly_budget": 1000},
        )

        assert response.status_code == 422

    def test_create_invalid_budget(self, client):
        """
        Tests that a 422 error is thrown when an invalid budget is used to create a user
        """
        response = client.post(
            "/users/",
            json={"name": "kimmy", "email": "kimmy@gmail.com", "monthly_budget": -200},
        )

        assert response.status_code == 422

    def test_create_with_database_error(self, broken_write_db_client):
        """
        Tests that a 500 error is thrown whenever a database error occurs during this POST request
        """
        test_new_user = UserCreate(
            name="test123", email="test123@gmail.com", monthly_budget=200
        )
        response = broken_write_db_client.post(
            "/users/", json=test_new_user.model_dump()
        )

        assert response.status_code == 500
        assert response.json()["detail"] == "Database error occurred!"


class TestUpdateUser:
    def test_successful_update_of_existing_user(self, client, generate_test_user):
        """
        Tests successful update of an existing user by checking if the 'monthly_budget' attribute of the response object has been updated
        """
        existing_user_id = generate_test_user["id"]
        update_data = UserUpdate(monthly_budget=250)
        response = client.put(
            f"/users/{existing_user_id}",
            json=update_data.model_dump(exclude_unset=True),
        )

        assert response.status_code == 200
        assert response.json()["monthly_budget"] == 250

    def test_update_nonexistent_user(self, client):
        """
        Tests that a 404 error will be thrown when updating a user that does not exist in the db
        """
        nonexistent_user = str(uuid.uuid4())
        update_data = UserUpdate(monthly_budget=250, name="kim")
        response = client.put(
            f"/users/{nonexistent_user}", json=update_data.model_dump()
        )

        assert response.status_code == 404

    def test_update_with_invalid_monthly_budget(self, client, generate_test_user):
        """
        Tests that a 422 error will be thrown when updating existing user information with invalid values
        """
        existent_user_id = generate_test_user["id"]
        response = client.put(
            f"/users/{existent_user_id}",
            json={"monthly_budget": -250},
        )

        assert response.status_code == 422

    def test_update_with_database_error(self, broken_write_db_client):
        """
        Tests that a 500 error is thrown whenever a database error occurs during this PUT request
        """
        fake_user_id = str(uuid.uuid4())
        update_data = UserUpdate(monthly_budget=200, name="kim")
        response = broken_write_db_client.put(
            f"/users/{fake_user_id}", json=update_data.model_dump()
        )

        # the only job is to ensure that when db commit fails, the endpoint returns a error 500.
        # does not matter which user is being updated, something just needs to be returned from the
        # query so the code does not bail on the 404 check and reach db.commit()

        assert response.status_code == 500
        assert response.json()["detail"] == "Database error occurred!"
