from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token)
def register(data: UserCreate, db: Session = Depends(get_db)):
    if auth_service.get_user_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = auth_service.create_user(db, data)
    token = auth_service.create_access_token({"sub": user.email})
    return Token(
        access_token=token,
        user=UserResponse(id=user.id, name=user.name, email=user.email),
    )


@router.post("/login", response_model=Token)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = auth_service.get_user_by_email(db, data.email)
    if not user or not auth_service.verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = auth_service.create_access_token({"sub": user.email})
    return Token(
        access_token=token,
        user=UserResponse(id=user.id, name=user.name, email=user.email),
    )
