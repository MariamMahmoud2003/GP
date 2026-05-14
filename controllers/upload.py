from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException
)

from ml.model import predict_oct
from sqlalchemy.orm import Session

import os
import shutil
import uuid

from database.database import SessionLocal
from models import models
from schemas import schemas

from core.dependencies import (
    get_db,
    get_current_user
)

router = APIRouter(
    prefix="/history",
    tags=["History"]
)


@router.post(
    "/upload",
    response_model=schemas.HistoryOut
)
def upload_history(

    # patient info
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    eye_side: str = Form(...),

    # image
    file: UploadFile = File(...),

    db: Session = Depends(get_db),

    current_user: models.Doctor = Depends(
        get_current_user
    )
):

    # ---------------- CHECK IF PATIENT EXISTS ----------------

    patient = db.query(models.Patient).filter(
        models.Patient.name == name,
        models.Patient.age == age,
        models.Patient.gender == gender
    ).first()

    # ---------------- CREATE PATIENT IF NOT FOUND ----------------

    if not patient:

        patient = models.Patient(
            name=name,
            age=age,
            gender=gender
        )

        db.add(patient)
        db.commit()
        db.refresh(patient)

    # ---------------- SAVE IMAGE ----------------

    upload_dir = "uploads"

    os.makedirs(upload_dir, exist_ok=True)

    unique_filename = (
        f"{uuid.uuid4()}_{file.filename}"
    )

    file_path = os.path.join(
        upload_dir,
        unique_filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )
    disease, confidence = predict_oct(file_path)

    # ---------------- CREATE HISTORY ----------------

    history = models.History(

        image_url=file_path,

        # doctor from JWT
        doctor_id=current_user.id,

        disease=disease,
        confidence=confidence,

        # which eye
        eye_side=eye_side,

        # patient from DB
        patient_id=patient.id
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return {
        "status": "success",
        "diagnosis": disease,
        "confidence": confidence,
        "history_id": history.id
    }

