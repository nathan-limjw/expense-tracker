import calendar
from datetime import datetime, timezone

from langchain_core.runnables import RunnableConfig
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.agent.report_agent.schemas import CategoryData, RawData, ReportAgentState
from app.models.budget import Budget
from app.models.expense import Expense
from app.models.user import User
from utils.logger import get_logger

logger = get_logger(__name__)


def accountant_node(state: ReportAgentState, config: RunnableConfig):
    logger.info("[ACCOUNTANT NODE] Compiling all your expenses...")

    db: Session = config["configurable"]["db"]
    user_id = state["input"].user_id
    month_str = state["input"].month

    year, month = map(int, month_str.split("-"))

    # Math with Date
    days_in_period = calendar.monthrange(year, month)[1]
    now = datetime.now(timezone.utc)
    if year == now.year and month == now.month:
        current_day = now.day  # referencing the current month
    else:
        current_day = days_in_period  # historical month

    try:
        # Calculating User's monthly budget
        user = db.query(User).filter(User.id == user_id).first()
        user_monthly_budget = user.monthly_budget if user.monthly_budget else None

        # Calculating User's monthly expenditure
        total_monthly_expenditure = (
            db.query(func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                extract("year", Expense.date) == year,
                extract("month", Expense.date) == month,
            )
            .scalar()
            or 0.0
        )

        # Calculating User's Per-Category expenditure
        expenditure_per_category = (
            db.query(Expense.category, func.sum(Expense.amount))
            .filter(
                Expense.user_id == user_id,
                extract("year", Expense.date) == year,
                extract("month", Expense.date) == month,
            )
            .group_by(Expense.category)
            .all()
        )

        # Category Budget for month
        all_category_budgets_for_month = (
            db.query(Budget)
            .filter(Budget.user_id == user_id, Budget.month == month_str)
            .all()
        )

    except Exception as e:
        logger.error(f"[ACCOUNTANT NODE] DB query failed: {e}")
        raise

    budget_map = {
        cat_budget.category: cat_budget.limit
        for cat_budget in all_category_budgets_for_month
    }

    categories: list[CategoryData] = []
    for category, spent in expenditure_per_category:
        budget = budget_map.get(category)
        variance = round(spent - budget, 2) if budget else None
        variance_pct = round((spent / budget) * 100, 1) if budget else None

        categories.append(
            {
                "category": category,
                "spent": spent,
                "budget": budget,
                "variance": variance,
                "variance_pct": variance_pct,
            }
        )

    raw_data: RawData = {
        "total_spent": round(total_monthly_expenditure, 2),
        "monthly_budget": user_monthly_budget,
        "categories": categories,
        "days_in_period": days_in_period,
        "current_day": current_day,
    }

    return {"raw_data": raw_data}
