from datetime import datetime, timezone

from pydantic import BaseModel, field_validator


class ReportCreate(BaseModel):
    user_id: str
    month: str = ""

    @field_validator("month", mode="before")
    @classmethod
    def default_to_current_month(cls, v):
        if not v:
            return datetime.now(timezone.utc).strftime("%Y-%m")
        try:
            datetime.strptime(v, "%Y-%m")
        except ValueError:
            raise ValueError("month must be in YYYY-MM format")
        return v


class CategoryReport(BaseModel):
    category: str
    spent: float
    budget: float | None
    variance: float | None
    variance_pct: float | None


class ReportResponse(BaseModel):
    month: str
    total_spent: float
    monthly_budget: float | None
    days_in_period: int
    current_day: int
    categories: list[CategoryReport]
    summary: str
    charts: dict
