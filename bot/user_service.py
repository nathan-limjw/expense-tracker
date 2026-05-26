import httpx
from sqlalchemy import Column, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from bot.config import settings

Base = declarative_base()


class TelegramUser(Base):
    __tablename__ = "telegram_users"

    telegram_user_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)


engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_id(telegram_user_id: str) -> str | None:
    db = SessionLocal()

    try:
        record = (
            db.query(TelegramUser)
            .filter(TelegramUser.telegram_user_id == telegram_user_id)
            .first()
        )
        return record.user_id if record else None
    finally:
        db.close()


async def register_user(telegram_user_id: str, name: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.API_BASE_URL}/users/",
            json={
                "name": name,
                "email": f"{telegram_user_id}@telegram.user",
                "monthly_budget": None,
            },
        )
        response.raise_for_status()
        user_id = response.json()["id"]

    db = SessionLocal()

    try:
        record = TelegramUser(
            telegram_user_id=telegram_user_id, user_id=user_id, name=name
        )
        db.add(record)
        db.commit()
    finally:
        db.close()

    return user_id


async def get_or_register_user(telegram_user_id: str, name: str) -> str:
    user_id = get_user_id(telegram_user_id)
    if not user_id:
        user_id = await register_user(telegram_user_id, name)
    return user_id
