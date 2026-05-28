from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agent.report_agent.graph import create_report_agent_graph
from app.db.database import get_db
from app.models.user import User
from app.schemas.report_schema import ReportCreate, ReportResponse
from utils.logger import get_logger

logger = get_logger(__name__)
graph = create_report_agent_graph()

report_router = APIRouter(prefix="/report")


@report_router.post("/", response_model=ReportResponse)
def get_report(input: ReportCreate, db: Session = Depends(get_db)):
    logger.info("Drafting a report of your financial habits...")
    try:
        user = db.query(User).filter(User.id == input.user_id).first()
    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        raise HTTPException(status_code=500, detail="Database error occurred!")

    if not user:
        logger.warning("User not found!")
        raise HTTPException(status_code=404, detail="User not found!")

    input_state = {"input": input}

    try:
        logger.info("Invoking report agent...")
        response = graph.invoke(input_state, config={"configurable": {"db": db}})

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception:
        logger.exception("Unexpected error during graph execution!")
        raise HTTPException(status_code=500, detail="Failed to generate report")

    final_report = response["final_report"]

    return ReportResponse(
        month=final_report["month"],
        total_spent=final_report["total_spent"],
        monthly_budget=final_report["monthly_budget"],
        days_in_period=final_report["days_in_period"],
        current_day=final_report["current_day"],
        categories=final_report["categories"],
        summary=final_report["summary"],
        charts=final_report["charts"],
        chart_bytes=final_report.get("chart_bytes"),
    )
