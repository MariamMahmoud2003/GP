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

from ml.model import model  # your loaded keras model
from ml.gradcam import generate_gradcam, save_gradcam_overlay
import numpy as np

from core.dependencies import (
    get_db,
    get_current_user
)

import cv2

router = APIRouter(
    prefix="/history",
    tags=["History"]
)


@router.post(
    "/upload"
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

    # ===================== NEW: GRAD-CAM =====================
    # preprocess for gradcam (same style as model input)
    img = cv2.imread(file_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.resize(img, (256, 256))
    img = img.astype("float32") / 255.0
    img = np.expand_dims(img, axis=-1)
    img = np.expand_dims(img, axis=0)

    # auto-detect last conv layer
    heatmap = generate_gradcam(model, img)

    base_name, _ = os.path.splitext(file_path)
    gradcam_path = f"{base_name}_gradcam.jpg"

    save_gradcam_overlay(file_path, heatmap, gradcam_path)

    # ---------------- CREATE HISTORY ----------------

    history = models.History(

        image_url=file_path,
        gradcam_url=gradcam_path,
        # doctor from JWT
        doctor_id=current_user.id,

        disease=disease,
        confidence=confidence,
        percentage=int(confidence * 100),

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
        "confidence": int(confidence * 100),
        "history_id": history.id,
        "gradcam_url": gradcam_path
    }

