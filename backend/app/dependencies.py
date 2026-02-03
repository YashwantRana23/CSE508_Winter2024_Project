from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services import auth_service

security = HTTPBearer(auto_error=False)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Return user if valid JWT provided; else None."""
    if not credentials:
        return None
    payload = auth_service.decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    return auth_service.get_user_by_email(db, payload["sub"])


def get_current_user(
    user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Require valid JWT; raise 401 if missing or invalid."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
