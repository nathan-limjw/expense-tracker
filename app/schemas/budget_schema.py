from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BudgetBase(BaseModel):
    category: Literal[
        "Food", "Transport", "Shopping", "Utilities", "Entertainment", "Others"
    ]
    month: str
    limit: float = Field(default=0.1, gt=0)
    user_id: str

    @field_validator("month")
    @classmethod
    def validate_month_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m")
        except ValueError:
            raise ValueError("month must be in YYYY-MM format")
        return v


class BudgetCreate(BudgetBase):
    pass


class BudgetResponse(BudgetBase):
    id: str

    model_config = ConfigDict(from_attributes=True)


class BudgetUpdate(BaseModel):
    category: Literal[
        "Food", "Transport", "Shopping", "Utilities", "Entertainment", "Others"
    ]
    month: str
    limit: float = Field(default=0.1, gt=0)

    @field_validator("month")
    @classmethod
    def validate_month_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m")
        except ValueError:
            raise ValueError("month must be in YYYY-MM format")
        return v
