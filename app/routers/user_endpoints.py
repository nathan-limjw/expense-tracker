from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.user_schema import UserCreate, UserResponse, UserUpdate

user_router = APIRouter(prefix="/users")


@user_router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    try:
        retrieved_user = db.query(User).filter(User.id == user_id).first()

    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database error occurred!")

    if not retrieved_user:
        raise HTTPException(status_code=404, detail="User not found!")

    return retrieved_user


@user_router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(
        name=user.name, email=user.email, monthly_budget=user.monthly_budget
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already registered!")

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred!")


@user_router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: str, new_details: UserUpdate, db: Session = Depends(get_db)):
    try:
        retrieved_user = db.query(User).filter(User.id == user_id).first()

        if not retrieved_user:
            raise HTTPException(status_code=404, detail="User not found!")

        update_data = new_details.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(retrieved_user, key, value)

        db.commit()
        db.refresh(retrieved_user)

        return retrieved_user

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error occurred!")
