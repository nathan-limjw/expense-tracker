from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Budget, User
from app.schemas.budget_schema import BudgetCreate, BudgetResponse, BudgetUpdate

budget_router = APIRouter(prefix="/budgets")


@budget_router.get("/{user_id}", response_model=List[BudgetResponse])
def get_all_budgets(user_id: str, db: Session = Depends(get_db)):
    try:
        budgets_by_category_for_user = (
            db.query(Budget).filter(Budget.user_id == user_id).all()
        )
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error occurred!")

    if not budgets_by_category_for_user:
        raise HTTPException(
            status_code=404, detail="User has not set any budgets by category!"
        )

    return budgets_by_category_for_user


@budget_router.post("/", response_model=BudgetResponse)
def create_category_budget(budget: BudgetCreate, db: Session = Depends(get_db)):
    new_budget = Budget(
        category=budget.category,
        month=budget.month,
        limit=budget.limit,
        user_id=budget.user_id,
    )

    try:
        user = db.query(User).filter(User.id == budget.user_id).first()
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error occurred!")

    if not user:
        raise HTTPException(status_code=404, detail="User not found!")

    try:
        db.add(new_budget)
        db.commit()
        db.refresh(new_budget)

        return new_budget

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Budget for this category already exists!"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred!")


@budget_router.put("/{user_id}", response_model=BudgetResponse)
def update_category_budget(
    user_id: str, new_budget: BudgetUpdate, db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found!")

        budget_to_update = (
            db.query(Budget)
            .filter(
                Budget.user_id == user_id,
                Budget.category == new_budget.category,
                Budget.month == new_budget.month,
            )
            .first()
        )

        if not budget_to_update:
            raise HTTPException(
                status_code=404, detail=f"Budget for {new_budget.category} not set!"
            )

        budget_to_update.limit = new_budget.limit

        db.commit()
        db.refresh(budget_to_update)

        return budget_to_update

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred!")
