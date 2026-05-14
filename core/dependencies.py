from fastapi import Depends, HTTPException, status

from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session

from database.database import SessionLocal

from core import auth
from models.models import Doctor


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)


# ---------------- DATABASE SESSION ----------------

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ---------------- CURRENT USER ----------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    payload = auth.verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    doctor_id = payload.get("sub")

    if doctor_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    doctor = db.query(Doctor).filter(
        Doctor.id == int(doctor_id)
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Doctor not found"
        )

    return doctor
