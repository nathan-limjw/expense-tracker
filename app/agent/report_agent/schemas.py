from typing import TypedDict

from app.schemas.report_schema import ReportCreate


class CategoryData(TypedDict):
    category: str
    spent: float
    budget: float | None
    variance: float | None
    variance_pct: float | None


class RawData(TypedDict):
    total_spent: float
    monthly_budget: float | None
    categories: list[CategoryData]
    days_in_period: int
    current_day: int


class ReportAgentState(TypedDict):
    input: ReportCreate
    raw_data: RawData
    financial_advice: str
    chart_image_bytes: dict
    final_report: dict
