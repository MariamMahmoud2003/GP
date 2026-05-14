from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from sqlalchemy.orm import Session

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

import os
from starlette.responses import FileResponse

from models import models

from core.dependencies import (
    get_db,
    get_current_user
)

router = APIRouter(
    prefix="/history",
    tags=["History"]
)


@router.get("/generate-report/{history_id}")
def generate_report(
    history_id: int,
    db: Session = Depends(get_db),
    current_user: models.Doctor = Depends(get_current_user)
):
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
            detail="History not found or not accessible"
        )

    patient = (
        db.query(models.Patient)
        .filter(models.Patient.id == history.patient_id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=404,
            detail="Patient not found"
        )

    os.makedirs("reports", exist_ok=True)

    file_path = os.path.join("reports", f"report_{history.id}.pdf")

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    content = [Paragraph("Medical Report", styles["Title"]), Spacer(1, 12),
               Paragraph(f"Patient Name: {patient.name}", styles["Normal"]),
               Paragraph(f"Age: {patient.age}", styles["Normal"]),
               Paragraph(f"Gender: {patient.gender}", styles["Normal"]), Spacer(1, 12),
               Paragraph(f"Disease: {history.disease}", styles["Normal"]),
               Paragraph(f"Confidence: {history.confidence}", styles["Normal"]),
               Paragraph(f"Eye Side: {history.eye_side}", styles["Normal"]), Spacer(1, 12)]

    if history.image_url and os.path.exists(history.image_url):
        content.append(Image(history.image_url, width=200, height=200))

    doc.build(content)

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"report_{history.id}.pdf"
    )

