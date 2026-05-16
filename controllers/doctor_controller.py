from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import schemas.schemas as schemas
import models.models as models

from core.dependencies import (
    get_db,
    get_current_user
)

from core import auth
import os

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
    response_model=schemas.DoctorProfile
)
def get_profile(
    db: Session = Depends(get_db),
    current_user: models.Doctor = Depends(
        get_current_user
    )
):
    unique_patients_count = (
        db.query(models.History.patient_id)
        .filter(models.History.doctor_id == current_user.id)
        .distinct()
        .count()
    )

    # Attach this value to our current_user object so Pydantic can read it
    current_user.number_of_patients = unique_patients_count

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


# @router.get("/patients/search", response_model=List[schemas.PatientOut])
# def search_patient_by_name(
#     name: str,
#     db: Session = Depends(get_db),
#     current_user: models.Doctor = Depends(get_current_user)
# ):
#     # We use .ilike(f"%{name}%") for a case-insensitive search
#     # Example: searching "john" will find "John Doe", "johnny", etc.
#     patients = (
#         db.query(models.Patient)
#         .join(models.History)
#         .filter(
#             models.Patient.name.ilike(f"%{name}%"),
#             models.History.doctor_id == current_user.id
#         )
#         .distinct() # Ensures the same patient isn't duplicated if they have multiple histories
#         .all()
#     )
#
#     if not patients:
#         raise HTTPException(
#             status_code=404,
#             detail="No patients found with that name under your care"
#         )
#
#     return patients


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


@router.get("/search", response_model=List[schemas.HistoryOut])
def search_history(
    patient_name: Optional[str] = Query(None, description="Search by case-insensitive patient name"),
    min_confidence: Optional[int] = Query(None, description="Minimum confidence score threshold (e.g. 85)"),
    start_date: Optional[date] = Query(None, description="Filter from this date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="Filter up to this date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: models.Doctor = Depends(get_current_user)
):
    # Base query: Always lock history records to the logged-in doctor
    query = (
        db.query(models.History)
        .join(models.Patient)
        .filter(models.History.doctor_id == current_user.id)
    )

    # 1. Filter by Patient Name (Case-insensitive partial match)
    if patient_name:
        query = query.filter(models.Patient.name.ilike(f"%{patient_name}%"))

    # 2. Filter by Minimum Confidence Score
    if min_confidence is not None:
        query = query.filter(models.History.percentage >= min_confidence)

    # 3. Filter by Date Range
    if start_date:
        query = query.filter(models.History.created_at >= start_date)
    if end_date:
        # Note: We append a time boundary or treat it carefully
        # to catch records all the way up to the end of that specific day
        query = query.filter(models.History.created_at <= end_date)

    # Execute and fetch records sorted by newest first
    results = query.order_by(models.History.created_at.desc()).all()

    if not results:
        raise HTTPException(
            status_code=404,
            detail="No history records found matching your search criteria"
        )

    return results


@router.delete("/delete/{history_id}", status_code=status.HTTP_200_OK)
def delete_history_record(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: models.Doctor = Depends(get_current_user)
):
    # 1. Secure the record: Make sure the record exists AND belongs to the active doctor
    history = (
        db.query(models.History)
        .filter(
            models.History.id == history_id,
            models.History.doctor_id == current_user.id
        )
        .first()
    )

    if not history:
        raise HTTPException(
            status_code=404,
            detail="History record not found or access denied"
        )

    # 2. Hard-drive cleanup: Wipe original image and Grad-CAM image from server disk
    if history.image_url and os.path.exists(history.image_url):
        try: os.remove(history.image_url)
        except Exception: pass  # Prevents crash if file is locked

    if history.gradcam_url and os.path.exists(history.gradcam_url):
        try: os.remove(history.gradcam_url)
        except Exception: pass

    # 3. Database cleanup: Drop the record row
    db.delete(history)
    db.commit()

    return {
        "status": "success",
        "message": f"Record {history_id} successfully deleted."
    }
