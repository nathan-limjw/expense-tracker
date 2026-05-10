from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, get_db
from app.main import app
from app.schemas.budget_schema import BudgetCreate
from app.schemas.user_schema import UserCreate


@pytest.fixture
def mock_llm(mocker):
    return mocker.patch("app.agent.expense_agent.nodes.llm")


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
