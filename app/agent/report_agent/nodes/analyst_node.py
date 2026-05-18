from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.report_agent.prompts import ANALYST_SYSTEM_PROMPT
from app.agent.report_agent.schemas import ReportAgentState
from app.agent.setup_llm import get_llm
from utils.logger import get_logger

logger = get_logger(__name__)
llm = get_llm()


def analyst_node(state: ReportAgentState):
    logger.info("[ANALYST NODE] Generating financial advice...")
    raw_data = state["raw_data"]
    month = state["input"].month

    populated_user_query = _build_human_message(raw_data, month)

    try:
        response = llm.invoke(
            [SystemMessage(ANALYST_SYSTEM_PROMPT), HumanMessage(populated_user_query)]
        )
    except Exception as e:
        logger.error(f"[ANALYST NODE] LLM Call failed: {e}")
        raise

    return {"financial_advice": response.content}


def _build_human_message(raw_data: dict, month: str):
    day = raw_data["current_day"]
    total_days = raw_data["days_in_period"]
    total_spent = raw_data["total_spent"]
    monthly_budget = raw_data["monthly_budget"]

    category_lines = "\n".join(
        [
            f"""
        Category: {c["category"]}
        - Total Spent: ${c["spent"]:.2f}
        - Budget: {f"${c['budget']:.2f}" if c["budget"] else "Not set"}
        - Variance Percentage: {f"{c['variance_pct']:.1f}%" if c["budget"] else "N/A"}
        """
            for c in raw_data["categories"]
        ]
    )

    budget_lines = f"""
        Overall budget: {f"${monthly_budget}" if monthly_budget else "No overall budget set"}
        Total Spent: ${total_spent:.2f}
        Percentage Spent: {f"{(total_spent * 100 / monthly_budget):.1f}%" if monthly_budget else "N/A"}
        """

    return f"""
        Here is my spending data for {month} (Day {day} / {total_days}):

        Overall Budget Information:
        {budget_lines}

        Budget by Category Breakdown: 
        {category_lines}

        Give me a financial summary and provide 2-3 actionable tips
    """
