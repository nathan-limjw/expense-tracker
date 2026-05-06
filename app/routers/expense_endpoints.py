from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Expense, User
from app.schemas.expense_schema import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from utils.logger import get_logger

logger = get_logger(__name__)

expense_router = APIRouter(prefix="/expenses")


@expense_router.get("/", response_model=List[ExpenseResponse])
def get_expense_by_filter(
    user_id: str,
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    less_than_amount: float | None = Query(default=None),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    logger.info("Initialising searching workflow...")
    try:
        user = db.query(User).filter(User.id == user_id).first()
    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        raise HTTPException(status_code=500, detail="Database error occurred!")

    if not user:
        logger.warning("User not found!")
        raise HTTPException(status_code=404, detail="User not found!")

    logger.info("Found all expenses for the given user...")
    all_expenses_by_user = db.query(Expense).filter(Expense.user_id == user_id)

    logger.info("Filtering expenses based on your preferences...")
    if start_date:
        all_expenses_by_user = all_expenses_by_user.filter(Expense.date >= start_date)
    if end_date:
        all_expenses_by_user = all_expenses_by_user.filter(Expense.date <= end_date)
    if less_than_amount:
        all_expenses_by_user = all_expenses_by_user.filter(
            Expense.amount <= less_than_amount
        )
    if category:
        all_expenses_by_user = all_expenses_by_user.filter(Expense.category == category)

    logger.info("Compiling all relevant expenses...")
    filtered_expenses = all_expenses_by_user.all()

    if not filtered_expenses:
        logger.warning("No expenses found!")
        raise HTTPException(status_code=404, detail="No expenses found!")

    return filtered_expenses


@expense_router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense_by_id(expense_id: str, db: Session = Depends(get_db)):
    logger.info(f"Retrieving expense with id: {expense_id}")
    try:
        retrieved_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        raise HTTPException(status_code=500, detail="Database error occurred!")

    if not retrieved_expense:
        logger.warning("Expense not found!")
        raise HTTPException(status_code=404, detail="Expense not found!")

    return retrieved_expense


@expense_router.post("/", response_model=ExpenseResponse)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    logger.info("Creating expense...")
    try:
        user = db.query(User).filter(User.id == expense.user_id).first()
    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        raise HTTPException(status_code=500, detail="Database error occurred!")

    if not user:
        logger.warning("User not found!")
        raise HTTPException(
            status_code=404, detail="User not found, create a user first!"
        )

    return


@expense_router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: str, updated_expense: ExpenseUpdate, db: Session = Depends(get_db)
):
    logger.info(f"Updating expense with id: {expense_id}")
    try:
        retrieved_expense = db.query(Expense).filter(Expense.id == expense_id).first()

        if not retrieved_expense:
            logger.warning("Expense not found!")
            raise HTTPException(status_code=404, detail="Expense not found!")

        update_data = updated_expense.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(retrieved_expense, key, value)

        retrieved_expense.date = datetime.now()

        db.commit()
        db.refresh(retrieved_expense)

        return retrieved_expense

    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred!")


@expense_router.delete("/{expense_id}", response_model=ExpenseResponse)
def delete_expense(expense_id: str, db: Session = Depends(get_db)):
    logger.info(f"Deleting expense with id: {expense_id}")
    try:
        retrieved_expense = db.query(Expense).filter(Expense.id == expense_id).first()

        if not retrieved_expense:
            logger.warning("Expense not found!")
            raise HTTPException(status_code=404, detail="Expense not found!")

        db.delete(retrieved_expense)
        db.commit()
        return retrieved_expense

    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred!")
