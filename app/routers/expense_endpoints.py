from datetime import datetime
from typing import List, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agent.expense_agent.graph import create_expense_agent_graph
from app.db.database import engine, get_db
from app.models.budget import Budget
from app.models.expense import Expense
from app.models.user import User
from app.schemas.expense_schema import (
    ExpenseCreate,
    ExpenseCreateResponse,
    ExpenseResponse,
    ExpenseUpdate,
)
from utils.db_helpers import format_month
from utils.logger import get_logger

logger = get_logger(__name__)

expense_router = APIRouter(prefix="/expenses")

graph = create_expense_agent_graph()


@expense_router.get("/", response_model=List[ExpenseResponse])
def get_expense_by_filter(
    user_id: str,
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    less_than_amount: float | None = Query(default=None, gt=0),
    category: Literal[
        "Food", "Transport", "Shopping", "Utilities", "Entertainment", "Others"
    ]
    | None = Query(default=None),
    db: Session = Depends(get_db),
):
    logger.info("Initialising searching workflow...")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422, detail="start_date cannot be after end_date"
        )
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


@expense_router.post("/", response_model=ExpenseCreateResponse)
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

    input_state = {
        "input": expense,
        "iterations": 0,
    }

    try:
        logger.info("Invoking expense extraction agent...")
        response = graph.invoke(input_state)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error during graph execution!")
        raise HTTPException(status_code=500, detail=str(e))

    if not response["extracted_info"]:
        logger.error("Failed to extract expense information!")
        raise HTTPException(
            status_code=500, detail="Failed to extract expense information"
        )

    if response["flagged"]:
        logger.warning("Expense flagged by agent!")
        raise HTTPException(status_code=422, detail=response["flagged_reason"])

    try:
        messages = []
        new_expense = Expense(
            user_id=expense.user_id,
            amount=response["extracted_info"].amount,
            category=response["extracted_info"].category,
            description=response["extracted_info"].extracted_description,
            date=response["extracted_info"].date,
            confidence_score=response["extracted_info"].confidence_score,
            flagged=response["flagged"],
        )

        db.add(new_expense)
        db.commit()
        db.refresh(new_expense)

        current_month = new_expense.date.strftime("%Y-%m")

        if user.monthly_budget:
            total_spending_by_month = (
                db.query(func.sum(Expense.amount))
                .filter(
                    Expense.user_id == expense.user_id,
                    format_month(Expense.date, engine) == current_month,
                )
                .scalar()
                or 0.0
            )

            if total_spending_by_month > user.monthly_budget:
                messages.append(
                    f"Heads up! You have exceeded your monthly budget of ${user.monthly_budget:.2f} by ${(total_spending_by_month - user.monthly_budget):.2f}!"
                )
            elif total_spending_by_month > 0.8 * user.monthly_budget:
                messages.append(
                    f"You have spent {(total_spending_by_month * 80 / user.monthly_budget):.2f}% of your monthly budget!"
                )

            messages.append(
                f"You have spent ${total_spending_by_month:.2f} out of your total monthly budget of ${user.monthly_budget:.2f}!"
            )

        monthly_budget_for_category = (
            db.query(Budget)
            .filter(
                Budget.user_id == expense.user_id,
                Budget.category == new_expense.category,
                Budget.month == current_month,
            )
            .first()
        )

        if monthly_budget_for_category:
            total_spending_by_category_by_month = (
                db.query(func.sum(Expense.amount))
                .filter(
                    Expense.user_id == expense.user_id,
                    Expense.category == new_expense.category,
                    format_month(Expense.date, engine) == current_month,
                )
                .scalar()
            ) or 0

            if total_spending_by_category_by_month > monthly_budget_for_category.limit:
                messages.append(
                    f"Heads up! You have exceeded your monthly budget of ${monthly_budget_for_category.limit:.2f} for {new_expense.category} by ${(total_spending_by_category_by_month - monthly_budget_for_category.limit):.2f}!"
                )
            elif (
                total_spending_by_category_by_month
                > 0.8 * monthly_budget_for_category.limit
            ):
                messages.append(
                    f"You have spent {(total_spending_by_category_by_month * 80 / monthly_budget_for_category.limit):.2f}% of your monthly budget for category: {new_expense.category}!"
                )

            messages.append(
                f"You have spent ${total_spending_by_category_by_month:.2f} out of your monthly budget for {new_expense.category} of ${monthly_budget_for_category.limit:.2f}!"
            )

        return ExpenseCreateResponse(expense=new_expense, messages=messages)

    except SQLAlchemyError:
        db.rollback()
        logger.exception("Database error occurred!")
        raise HTTPException(status_code=500, detail="Database error occurred!")


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
