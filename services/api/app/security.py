from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User

def current_user(x_demo_user: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not settings.demo_mode:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "OIDC authentication must be configured.")
    if settings.student_only_mode:
        user = db.query(User).filter(User.email == "prototype.student@demo.local").one_or_none()
        if not user: raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The prototype is still being seeded. Refresh in a moment.")
        return user
    if not x_demo_user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Choose a development demo identity.")
    user = db.query(User).filter(User.email == x_demo_user.lower()).one_or_none()
    if not user: raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unknown demo identity.")
    if settings.student_only_mode and user.can_create_courses:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This prototype is limited to student access.")
    return user
