from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.db.database import init_db
from app.routers.budget_endpoints import budget_router
from app.routers.expense_endpoints import expense_router
from app.routers.report_endpoints import report_router
from app.routers.user_endpoints import user_router
from utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initialising application...")
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def home():
    return {"detail": "Welcome to your favorite Expense Tracker!"}


app.include_router(user_router)
app.include_router(expense_router)
app.include_router(budget_router)
app.include_router(report_router)
