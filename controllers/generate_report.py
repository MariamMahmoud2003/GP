from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from sqlalchemy.orm import Session

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
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

    title_text = '<font color="#003366">Medical Report</font>'
    original_title_text = '<font color="#006699">Original Image</font>'
    gradcam_title_text = '<font color="#D32F2F">AI Explanation (Grad-CAM)</font>'

    content = [
        Paragraph(title_text, styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Patient Name: {patient.name}", styles["Normal"]),
        Paragraph(f"Age: {patient.age}", styles["Normal"]),
        Paragraph(f"Gender: {patient.gender}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"Disease: {history.disease}", styles["Normal"]),
        Paragraph(f"Confidence: {history.percentage}%", styles["Normal"]),
        Paragraph(f"Eye Side: {history.eye_side}", styles["Normal"]),
        Spacer(1, 12)
    ]

    image_row = []

    if history.image_url and os.path.exists(history.image_url):
        left_col = [
            Paragraph(original_title_text, styles["Heading2"]),
            Spacer(1, 6),
            Image(history.image_url, width=210, height=190)
        ]
        image_row.append(left_col)
    else:
        image_row.append("")

    if history.gradcam_url and os.path.exists(history.gradcam_url):
        right_col = [
            Paragraph(gradcam_title_text, styles["Heading2"]),
            Spacer(1, 6),
            Image(history.gradcam_url, width=210, height=190)
        ]
        image_row.append(right_col)
    else:
        image_row.append("")

    if history.image_url or history.gradcam_url:
        # 460 total width splits perfectly onto an A4 page (230 width per column)
        img_table = Table([image_row], colWidths=[230, 230])
        img_table.hAlign = 'CENTER'
        content.append(img_table)

    doc.build(content)

    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=f"report_{history.id}.pdf"
    )

