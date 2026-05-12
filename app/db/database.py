from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from utils.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    **(
        {"connect_args": {"check_same_thread": False}}
        if "sqlite" in settings.DATABASE_URL
        else {}
    ),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
