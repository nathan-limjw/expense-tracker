from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.budget import Budget
from app.models.user import User
from app.schemas.budget_schema import BudgetCreate, BudgetResponse, BudgetUpdate
from utils.logger import get_logger

logger = get_logger(__name__)

budget_router = APIRouter(prefix="/budgets")


@budget_router.get("/{user_id}", response_model=List[BudgetResponse])
def get_all_budgets(user_id: str, db: Session = Depends(get_db)):
    logger.info(f"Retrieving all budgets set by user: {user_id}")
    try:
        budgets_by_category_for_user = (
            db.query(Budget).filter(Budget.user_id == user_id).all()
        )
    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        raise HTTPException(status_code=500, detail="Database error occurred!")

    if not budgets_by_category_for_user:
        logger.warning("User has not set any budgets by category!")
        raise HTTPException(
            status_code=404, detail="User has not set any budgets by category!"
        )

    return budgets_by_category_for_user


@budget_router.post("/", response_model=BudgetResponse)
def create_category_budget(budget: BudgetCreate, db: Session = Depends(get_db)):
    logger.info(
        f"Creating a new budget for category: {budget.category}, month: {budget.month}..."
    )
    new_budget = Budget(
        category=budget.category,
        month=budget.month,
        limit=budget.limit,
        user_id=budget.user_id,
    )

    try:
        user = db.query(User).filter(User.id == budget.user_id).first()
    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        raise HTTPException(status_code=500, detail="Database error occurred!")

    if not user:
        logger.warning("User not found!")
        raise HTTPException(status_code=404, detail="User not found!")

    try:
        logger.info("Adding new budget to database...")
        db.add(new_budget)
        db.commit()
        db.refresh(new_budget)

        logger.info(
            f"Successfully created new budget for category: {budget.category}, month: {budget.month}, limit: {budget.limit}"
        )
        return new_budget

    except IntegrityError:
        logger.warning("Budget for this category already exists!")
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Budget for this category already exists!"
        )
    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred!")


@budget_router.put("/{user_id}", response_model=BudgetResponse)
def update_category_budget(
    user_id: str, new_budget: BudgetUpdate, db: Session = Depends(get_db)
):
    try:
        logger.info(
            f"Updating budget for category: {new_budget.category}, month: {new_budget.month}..."
        )
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            logger.warning("User not found!")
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
            logger.warning(f"Budget for {new_budget.category} not set!")
            raise HTTPException(
                status_code=404, detail=f"Budget for {new_budget.category} not set!"
            )

        budget_to_update.limit = new_budget.limit

        db.commit()
        db.refresh(budget_to_update)

        logger.info(
            f"Successfully updated budget for category: {new_budget.category}, month: {new_budget.month}, limit: {new_budget.limit}"
        )

        return budget_to_update

    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred!")
