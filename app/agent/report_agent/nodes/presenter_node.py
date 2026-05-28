import base64

import boto3

from app.agent.report_agent.schemas import ReportAgentState
from utils.config import settings
from utils.logger import get_logger

logger = get_logger(__name__)

s3 = boto3.client("s3", region_name=settings.AWS_REGION)


def presenter_node(state: ReportAgentState):
    logger.info("[PRESENTER NODE] Assembling a report of your finances...")

    user_id = state["input"].user_id
    month = state["input"].month
    raw_data = state["raw_data"]

    try:
        pie_url = _upload_chart(
            image_bytes=state["chart_image_bytes"]["pie"],
            key=f"reports/{user_id}/{month}/pie.png",
        )

        bar_url = _upload_chart(
            image_bytes=state["chart_image_bytes"]["bar"],
            key=f"reports/{user_id}/{month}/bar.png",
        )

    except Exception as e:
        logger.error(f"[PRESENTER NODE] Error uploading visuals to S3: {e}")
        raise

    final_report = {
        "month": month,
        "total_spent": raw_data["total_spent"],
        "monthly_budget": raw_data["monthly_budget"],
        "days_in_period": raw_data["days_in_period"],
        "current_day": raw_data["current_day"],
        "categories": raw_data["categories"],
        "summary": state["financial_advice"],
        "charts": {"pie": pie_url, "bar": bar_url},
        "chart_bytes": {
            "pie": base64.b64encode(state["chart_image_bytes"]["pie"]).decode("utf-8"),
            "bar": base64.b64encode(state["chart_image_bytes"]["bar"]).decode("utf-8"),
        },
    }

    return {"final_report": final_report}


def _upload_chart(image_bytes: bytes, key: str):
    s3.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=key,
        Body=image_bytes,
        ContentType="image/png",
    )

    return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"
