import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import Settings
from app.models.models import User, ManufacturerLabel, ComplianceStatus, UserRole
from app.schemas.schemas import ManufacturerLabelResponse, ManufacturerLabelCreate
from app.api.routes.auth import get_current_user, require_roles
from app.services.ocr_service import run_ocr
from app.services.field_extractor import extract_all_fields
from app.services.compliance_engine import check_compliance

settings = Settings()
router = APIRouter(prefix="/manufacturer", tags=["Manufacturer Portal"])


@router.post("/check-label", response_model=ManufacturerLabelResponse)
async def check_label_compliance(
    image: UploadFile = File(...),
    product_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(image.filename)[1] if image.filename else ".jpg"
    filename = f"mfg_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    content = await image.read()
    with open(filepath, "wb") as f:
        f.write(content)

    ocr_result = run_ocr(filepath)
    raw_text = ocr_result.get("text", "")
    extracted_fields = extract_all_fields(raw_text)
    compliance = check_compliance(extracted_fields)

    label = ManufacturerLabel(
        user_id=user.id,
        product_name=product_name,
        label_image_path=filepath,
        compliance_status=ComplianceStatus(compliance["status"]),
        compliance_result={
            "extracted_fields": extracted_fields,
            "compliance": compliance,
            "ocr_text": raw_text,
        },
    )
    db.add(label)
    await db.commit()
    await db.refresh(label)

    return ManufacturerLabelResponse.model_validate(label)


@router.get("/labels", response_model=list[ManufacturerLabelResponse])
async def list_my_labels(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ManufacturerLabel)
        .where(ManufacturerLabel.user_id == user.id)
        .order_by(ManufacturerLabel.submitted_at.desc())
    )
    labels = result.scalars().all()
    return [ManufacturerLabelResponse.model_validate(l) for l in labels]


@router.get("/labels/{label_id}", response_model=ManufacturerLabelResponse)
async def get_label(
    label_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ManufacturerLabel).where(ManufacturerLabel.id == label_id)
    )
    label = result.scalar_one_or_none()
    if not label:
        raise HTTPException(status_code=404, detail="Label not found")
    if label.user_id != user.id and user.role not in (UserRole.ADMIN, UserRole.SUPERVISOR):
        raise HTTPException(status_code=403, detail="Not authorized")
    return ManufacturerLabelResponse.model_validate(label)
