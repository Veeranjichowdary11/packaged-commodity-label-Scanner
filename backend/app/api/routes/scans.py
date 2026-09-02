import os
import uuid
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional

from app.core.database import get_db
from app.core.config import Settings
from app.models.models import User, Product, Scan, Violation, Report, ComplianceStatus, ViolationSeverity
from app.schemas.schemas import ScanResponse, ScanCreate
from app.api.routes.auth import get_current_user
from app.services.ocr_service import run_ocr, detect_barcode, estimate_font_sizes
from app.services.field_extractor import extract_all_fields
from app.services.compliance_engine import check_compliance
from app.services.report_generator import generate_report_number, generate_pdf_report, compute_hash

settings = Settings()
router = APIRouter(prefix="/scans", tags=["Scanning"])


@router.post("/", response_model=ScanResponse)
@router.post("", response_model=ScanResponse)
async def create_scan(
    image: UploadFile = File(...),
    scan_type: str = Form("manual"),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    store_name: Optional[str] = Form(None),
    store_address: Optional[str] = Form(None),
    barcode: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(image.filename)[1] if image.filename else ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    content = await image.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    with open(filepath, "wb") as f:
        f.write(content)

    ocr_result = run_ocr(filepath)
    raw_text = ocr_result.get("text", "")
    extracted_fields = extract_all_fields(raw_text)

    barcode_detected = barcode or detect_barcode(filepath)

    product = None
    if barcode_detected:
        result = await db.execute(select(Product).where(Product.barcode == barcode_detected))
        product = result.scalar_one_or_none()
        if not product:
            product = Product(
                barcode=barcode_detected,
                name=extracted_fields.get("common_name"),
                manufacturer_name=extracted_fields.get("manufacturer", {}).get("value") if isinstance(extracted_fields.get("manufacturer"), dict) else None,
                net_quantity=extracted_fields.get("net_quantity", {}).get("raw") if isinstance(extracted_fields.get("net_quantity"), dict) else None,
                mrp=extracted_fields.get("mrp", {}).get("value") if isinstance(extracted_fields.get("mrp"), dict) else None,
            )
            db.add(product)
            await db.flush()

    compliance = check_compliance(extracted_fields)

    scan = Scan(
        user_id=user.id,
        product_id=product.id if product else None,
        image_path=filepath,
        scan_type=scan_type,
        latitude=latitude,
        longitude=longitude,
        store_name=store_name,
        store_address=store_address,
        raw_ocr_text=raw_text,
        extracted_fields=extracted_fields,
        barcode_detected=barcode_detected,
        compliance_status=ComplianceStatus(compliance["status"]),
        compliance_score=compliance["score"],
        total_checks=compliance["total_checks"],
        passed_checks=compliance["passed_checks"],
        failed_checks=compliance["failed_checks"],
    )
    db.add(scan)
    await db.flush()

    for v in compliance["violations"]:
        violation = Violation(
            scan_id=scan.id,
            rule_code=v["rule_code"],
            rule_name=v["rule_name"],
            description=v["description"],
            severity=ViolationSeverity(v["severity"]),
            field_name=v.get("field_name"),
            expected_value=v.get("expected_value"),
            actual_value=v.get("actual_value"),
            section_reference=v.get("section_reference"),
        )
        db.add(violation)

    report_number = generate_report_number()
    scan_data = {
        "scan_id": scan.id,
        "compliance_status": compliance["status"],
        "compliance_score": compliance["score"],
        "scan_type": scan_type,
        "store_name": store_name,
        "latitude": latitude,
        "longitude": longitude,
    }

    pdf_path = generate_pdf_report(
        scan_data=scan_data,
        violations=compliance["violations"],
        extracted_fields=extracted_fields,
        image_path=filepath,
        output_dir=settings.REPORTS_DIR,
        report_number=report_number,
    )

    report = Report(
        scan_id=scan.id,
        report_number=report_number,
        pdf_path=pdf_path,
        hash_chain=compute_hash(scan_data),
    )
    db.add(report)

    await db.commit()

    result = await db.execute(
        select(Scan).options(selectinload(Scan.violations)).where(Scan.id == scan.id)
    )
    scan = result.scalar_one()

    return ScanResponse.model_validate(scan)


@router.get("/", response_model=list[ScanResponse])
async def list_scans(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Scan).options(selectinload(Scan.violations)).order_by(Scan.created_at.desc())

    if user.role.value in ("consumer", "manufacturer"):
        query = query.where(Scan.user_id == user.id)

    if status:
        query = query.where(Scan.compliance_status == ComplianceStatus(status))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    scans = result.scalars().all()
    return [ScanResponse.model_validate(s) for s in scans]


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Scan).options(selectinload(Scan.violations)).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if user.role.value in ("consumer", "manufacturer") and scan.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return ScanResponse.model_validate(scan)


@router.get("/{scan_id}/report")
async def download_report(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from fastapi.responses import FileResponse

    result = await db.execute(select(Report).where(Report.scan_id == scan_id))
    report = result.scalar_one_or_none()
    if not report or not report.pdf_path:
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(
        report.pdf_path,
        media_type="application/pdf",
        filename=f"{report.report_number}.pdf",
    )
