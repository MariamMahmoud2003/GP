from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

import schemas.schemas as schemas
import models.models as models

from core.dependencies import (
    get_db,
    get_current_user
)

from core import auth


router = APIRouter(
    tags=["Doctors"]
)


@router.post("/login", response_model=schemas.Token)
def login(user: schemas.DoctorLogin, db: Session = Depends(get_db)):

    doctor = db.query(models.Doctor).filter(
        models.Doctor.username == user.username
    ).first()

    if not doctor:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not auth.verify_password(user.password, doctor.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token(
        {"sub": str(doctor.id)}
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get(
    "/me",
    response_model=schemas.DoctorResponse
)
def get_profile(
    current_user: models.Doctor = Depends(
        get_current_user
    )
):
    return current_user


@router.get("/history", response_model=list[schemas.HistoryOut])
def get_history(
    db: Session = Depends(get_db),
    current_user: models.Doctor = Depends(get_current_user)
):

    return db.query(models.History).filter(
        models.History.doctor_id == current_user.id
    ).all()


@router.get("/patients/{patient_id}")
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.Doctor = Depends(get_current_user)
):
    patient = (
        db.query(models.Patient)
        .join(models.History)
        .filter(
            models.Patient.id == patient_id,
            models.History.doctor_id == current_user.id
        )
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found or not accessible"
        )

    return patient


@router.get("/patients", response_model=list[schemas.PatientOut])
def get_patients(
    db: Session = Depends(get_db),
    current_user: models.Doctor = Depends(get_current_user)
):
    patients = (
        db.query(models.Patient)
        .join(models.History, models.History.patient_id == models.Patient.id)
        .filter(models.History.doctor_id == current_user.id)
        .distinct()
        .all()
    )

    return patients


@router.get("/doctor/stats")
def doctor_stats(
    db: Session = Depends(get_db),
    current_user: models.Doctor = Depends(get_current_user)
):
    patient_count = (
        db.query(func.count(func.distinct(models.History.patient_id)))
        .filter(models.History.doctor_id == current_user.id)
        .scalar()
    )

    history_count = (
        db.query(func.count(models.History.id))
        .filter(models.History.doctor_id == current_user.id)
        .scalar()
    )

    return {
        "total_patients": patient_count,
        "total_histories": history_count
    }
