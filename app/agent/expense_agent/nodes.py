from datetime import datetime, timezone
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.agent.expense_agent.prompts import EXTRACTION_PROMPT, RETRY_EXTRACTION_PROMPT
from app.agent.expense_agent.schemas import (
    ExpenseAgentState,
    ExtractedExpense,
)
from utils.config import (
    CONFIDENCE_THRESHOLD,
    MODEL_TEMPERATURE,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)
from utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


llm = ChatOllama(
    model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL, temperature=MODEL_TEMPERATURE
)


def extraction_node(state: ExpenseAgentState):
    structured_llm = llm.with_structured_output(ExtractedExpense)
    expense_description = state["input"].description
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    logger.debug(f"Today's time: {today}")
    logger.debug(f"Expense description: {expense_description}")

    if state["iterations"] > 0:
        logger.info(f"[ATTEMPT {state['iterations'] + 1}] Retrying extraction... ")
        filled_retry_extraction_prompt = RETRY_EXTRACTION_PROMPT.format(
            flagged_reason=state["flagged_reason"], current_date=today
        )
        response = structured_llm.invoke(
            [
                SystemMessage(filled_retry_extraction_prompt),
                HumanMessage(expense_description),
            ]
        )

    else:
        logger.info("Extracting information...")
        filled_extraction_prompt = EXTRACTION_PROMPT.format(current_date=today)
        response = structured_llm.invoke(
            [SystemMessage(filled_extraction_prompt), HumanMessage(expense_description)]
        )

    return {
        "extracted_info": response,
        "iterations": state["iterations"] + 1,
        "flagged": False,
        "flagged_reason": None,
    }


def validation_node(state: ExpenseAgentState):
    logger.info("Validating information...")

    extracted_info = state["extracted_info"]
    logger.debug(f"Extracted info: {extracted_info}")

    if extracted_info is None:
        return {
            "flagged": True,
            "flagged_reason": "Unable to extract information. Please rephrase your input.",
        }

    if extracted_info.amount is None or extracted_info.amount <= 0:
        return {
            "flagged": True,
            "flagged_reason": "Could not extract a valid amount. Please include a valid and proper amount for extraction.",
        }

    if extracted_info.category is None:
        return {
            "flagged": True,
            "flagged_reason": "Could not determine a category. Be more specific.",
        }

    if extracted_info.confidence_score < CONFIDENCE_THRESHOLD:
        return {
            "flagged": True,
            "flagged_reason": "Input was unclear. Please rephrase and try again.",
        }

    return {"flagged": False, "flagged_reason": None}


def decision_node(state: ExpenseAgentState) -> Literal["END", "extraction"]:
    if not state["flagged"]:  # successful after one attempt of extraction
        return "END"
    if state["iterations"] >= 3:  # more than 3 tries
        logger.warning(
            "Maximum attempts reached. Please check your input and try again!"
        )
        return "END"
    return "extraction"  # have yet to reach 3 attempts of extraction
