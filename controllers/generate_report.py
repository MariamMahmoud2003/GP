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

    doc = SimpleDocTemplate(file_path, topMargin=35, bottomMargin=35)
    styles = getSampleStyleSheet()
    content = [
        Paragraph("Medical Report", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Patient Name: {patient.name}", styles["Normal"]),
        Paragraph(f"Age: {patient.age}", styles["Normal"]),
        Paragraph(f"Gender: {patient.gender}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"Disease: {history.disease}", styles["Normal"]),
        Paragraph(f"Confidence: {history.confidence:.2%}", styles["Normal"]),  # Optional: Format as percentage
        Paragraph(f"Eye Side: {history.eye_side}", styles["Normal"]),
        Spacer(1, 12)
    ]
    if history.image_url and os.path.exists(history.image_url):
        content.append(Paragraph("Original Image", styles["Heading2"]))
        img = Image(history.image_url, width=220, height=200)
        img.hAlign = 'CENTER'  # Centers the image
        content.append(img)

    if history.gradcam_url and os.path.exists(history.gradcam_url):
        content.append(Spacer(1, 12))
        content.append(Paragraph("AI Explanation (Grad-CAM)", styles["Heading2"]))

        grad_img = Image(history.gradcam_url, width=220, height=200)
        grad_img.hAlign = 'CENTER'  # Centers the image
        content.append(grad_img)

    doc.build(content)

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"report_{history.id}.pdf"
    )

