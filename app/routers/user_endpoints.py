from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate
from utils.logger import get_logger

logger = get_logger(__name__)

user_router = APIRouter(prefix="/users")


@user_router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    logger.info(f"Retrieving user with id: {user_id}...")
    try:
        retrieved_user = db.query(User).filter(User.id == user_id).first()

    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        raise HTTPException(status_code=500, detail="Database error occurred!")

    if not retrieved_user:
        logger.warning("User not found!")
        raise HTTPException(status_code=404, detail="User not found!")

    return retrieved_user


@user_router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info("Creating new user...")
    new_user = User(
        name=user.name, email=user.email, monthly_budget=user.monthly_budget
    )
    try:
        logger.info("Adding new user to database...")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info("User successfully added to database!")

        return new_user

    except IntegrityError:
        logger.warning("User already registered!")
        db.rollback()
        raise HTTPException(status_code=409, detail="User already registered!")

    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred!")


@user_router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, new_details: UserUpdate, db: Session = Depends(get_db)):
    logger.info("Initialising updating process...")
    try:
        logger.info(f"Retrieving user with id: {user_id}")
        retrieved_user = db.query(User).filter(User.id == user_id).first()

        if not retrieved_user:
            logger.warning("User not found!")
            raise HTTPException(status_code=404, detail="User not found!")

        logger.info("Parsing new details...")
        update_data = new_details.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(retrieved_user, key, value)

        logger.info("Updating user details...")
        db.commit()
        db.refresh(retrieved_user)

        logger.info("Successfully updated user details!")
        return retrieved_user

    except SQLAlchemyError:
        logger.exception("Database error occurred!")
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred!")
