from enum import verify

from fastapi import HTTPException
from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash, verify_password, create_access_token
from .models import UserSettingsLog, User
from .schemas import UserCreate, UserLogin, UserUpdate
from .config import oauth2_scheme


def signup_user(db:Session, user: UserCreate):
        db_user = db.query(User).filter(User.username == user.username).first()
        if (db_user):
            raise HTTPException(status_code=400, detail='Username already taken')

        db_user_by_email = db.query(User).filter(User.email == user.email).first()
        if (db_user_by_email):
            raise HTTPException(status_code=400, detail='Email already registered')

        hashed_password = get_password_hash(user.password)
        new_user = User(
            username = user.username,
            password = hashed_password,
            email = user.email
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user


def signin_user(db:Session, user: UserLogin):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail='Incorrect username or password')

    access_token = create_access_token(data={"sub": db_user.username, "is_admin": db_user.is_admin})
    return {"access_token": access_token, "token_type": "bearer"}

def get_users(db: Session):
    return db.query(models.User).all()

def get_user_achievements(db: Session, user_id: int) -> schemas.UserAchievement:
    achievements = db.query(models.UserAchievement).filter(models.UserAchievement.user_id == user_id).first()
    return achievements

def update_user(db: Session, user_id: int, update_data: UserUpdate):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        return None

    if update_data.username:
        user.username = update_data.username
    if update_data.email:
        user.email = update_data.email
    if update_data.password:
        user.password = get_password_hash(update_data.password)

    db.commit()
    db.refresh(user)
    return user


def get_user_logs(db: Session, user_id: int):
    return db.query(UserSettingsLog).filter(UserSettingsLog.user_id == user_id).all()


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user or password != user.password:
        return None
    return user
