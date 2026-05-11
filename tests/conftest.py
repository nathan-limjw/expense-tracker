from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app
from app.schemas.budget_schema import BudgetCreate
from app.schemas.expense_schema import ExpenseCreate
from app.schemas.user_schema import UserCreate
from tests.test_helpers import populate_extracted_expense, setup_mock


@pytest.fixture
def mock_llm(mocker):
    return mocker.patch("app.agent.expense_agent.nodes.llm")


@pytest.fixture
def mock_agent(mocker):
    return mocker.patch("app.routers.expense_endpoints.graph")


@pytest.fixture
def client():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def broken_read_db_client():
    "For GET endpoints, breaks at query"

    def broken_db():
        db = MagicMock()

        db.query.side_effect = SQLAlchemyError("DB is down")
        db.rollback.return_value = None

        yield db

    app.dependency_overrides[get_db] = broken_db

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def broken_write_db_client():
    "For POST/PUT endpoints, breaks at commit"

    def broken_db():
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = MagicMock()
        db.add.return_value = None
        db.commit.side_effect = SQLAlchemyError("DB is down")
        db.rollback.return_value = None
        yield db

    app.dependency_overrides[get_db] = broken_db

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def generate_test_user(client):
    test_user = UserCreate(name="kimmy", email="kimmy@gmail.com", monthly_budget=1000)
    created_test_user = client.post("/users/", json=test_user.model_dump())
    return created_test_user.json()


@pytest.fixture
def generate_test_budget(client, generate_test_user):
    test_id = generate_test_user["id"]
    test_budget = BudgetCreate(
        category="Food", month="2026-05", limit=200, user_id=test_id
    )
    created_test_budget = client.post("/budgets/", json=test_budget.model_dump())
    return created_test_budget.json()


@pytest.fixture
def generate_test_expense(client, generate_test_user, mocker, mock_llm):
    test_user_id = generate_test_user["id"]

    setup_mock(populate_extracted_expense(), mocker, mock_llm)

    test_expense = ExpenseCreate(
        description="Coffee for $2 after lunch today", user_id=test_user_id
    )

    created_test_expense = client.post("/expenses/", json=test_expense.model_dump())
    return created_test_expense.json()


@pytest.fixture
def generate_multiple_expenses(client, generate_test_user, mocker, mock_llm):
    test_user_id = generate_test_user["id"]
    expenses = []

    test_descriptions = [
        ("Coffee for $2 after lunch 11 May 2026", "Food", 2.0),
        ("Noodle Soup $6 after gym 11 May 2026", "Food", 6.0),
        ("Concession pass $81 10 May 2026", "Transport", 81.0),
        ("Groceries from NTUC $45 10 May 2026", "Shopping", 45.0),
        ("Credit Card bill $30.60 11 May 2026", "Utilities", 30.60),
    ]

    for description, category, amount in test_descriptions:
        setup_mock(
            populate_extracted_expense(category=category, amount=amount),
            mocker,
            mock_llm,
        )
        test_expense = ExpenseCreate(description=description, user_id=test_user_id)
        response = client.post("/expenses/", json=test_expense.model_dump())
        expenses.append(response.json())

    return expenses
