from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BudgetBase(BaseModel):
    category: str
    month: datetime
    limit: float
    user_id: str


class BudgetCreate(BudgetBase):
    pass


class BudgetResponse(BudgetBase):
    id: str

    model_config = ConfigDict(from_attributes=True)


class BudgetUpdate(BaseModel):
    category: str
    month: datetime
    limit: float
