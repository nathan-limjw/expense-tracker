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
