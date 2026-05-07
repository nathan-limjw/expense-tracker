from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class BudgetBase(BaseModel):
    category: str
    month: str
    limit: float
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
    category: str
    month: str
    limit: float

    @field_validator("month")
    @classmethod
    def validate_month_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m")
        except ValueError:
            raise ValueError("month must be in YYYY-MM format")
        return v
