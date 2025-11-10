# backend/app/api/controllers/authController.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import os

from app.db.session import get_db
from app.db.models.userModel import UserModel

# Load JWT config from environment (set via docker-compose or .env)
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-this-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Matches your /users/login route
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")         # you encode sub = user_email
        uid = payload.get("user_id")       # and also user_id
    except JWTError:
        raise credentials_exception

    user = None
    if uid is not None:
        user = db.query(UserModel).filter(UserModel.user_id == int(uid)).first()
    if user is None and email:
        user = db.query(UserModel).filter(UserModel.user_email == email).first()

    if not user:
        raise credentials_exception

    return user