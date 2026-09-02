from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.models import User, Scan, Violation, ComplianceStatus, ViolationSeverity, UserRole
from app.schemas.schemas import DashboardStats, ScanResponse
from app.api.routes.auth import get_current_user, require_roles

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.INSPECTOR, UserRole.SUPERVISOR, UserRole.ADMIN)),
):
    total_result = await db.execute(select(func.count(Scan.id)))
    total_scans = total_result.scalar() or 0

    compliant_result = await db.execute(
        select(func.count(Scan.id)).where(Scan.compliance_status == ComplianceStatus.COMPLIANT)
    )
    compliant_count = compliant_result.scalar() or 0

    non_compliant_result = await db.execute(
        select(func.count(Scan.id)).where(Scan.compliance_status == ComplianceStatus.NON_COMPLIANT)
    )
    non_compliant_count = non_compliant_result.scalar() or 0

    partial_result = await db.execute(
        select(func.count(Scan.id)).where(Scan.compliance_status == ComplianceStatus.PARTIALLY_COMPLIANT)
    )
    partial_count = partial_result.scalar() or 0

    compliance_rate = round((compliant_count / total_scans) * 100, 1) if total_scans > 0 else 0

    top_violations_result = await db.execute(
        select(Violation.rule_name, func.count(Violation.id).label("count"))
        .group_by(Violation.rule_name)
        .order_by(func.count(Violation.id).desc())
        .limit(10)
    )
    top_violations = [{"rule": row[0], "count": row[1]} for row in top_violations_result.all()]

    recent_result = await db.execute(
        select(Scan).options(selectinload(Scan.violations))
        .order_by(Scan.created_at.desc()).limit(10)
    )
    recent_scans = [ScanResponse.model_validate(s) for s in recent_result.scalars().all()]

    scan_type_result = await db.execute(
        select(Scan.scan_type, func.count(Scan.id)).group_by(Scan.scan_type)
    )
    scans_by_type = {row[0]: row[1] for row in scan_type_result.all()}

    sev_result = await db.execute(
        select(Violation.severity, func.count(Violation.id)).group_by(Violation.severity)
    )
    severity_breakdown = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in sev_result.all()}

    return DashboardStats(
        total_scans=total_scans,
        compliant_count=compliant_count,
        non_compliant_count=non_compliant_count,
        partial_count=partial_count,
        compliance_rate=compliance_rate,
        top_violations=top_violations,
        recent_scans=recent_scans,
        scans_by_type=scans_by_type,
        violation_severity_breakdown=severity_breakdown,
    )


@router.get("/heatmap")
async def get_violation_heatmap(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.INSPECTOR, UserRole.SUPERVISOR, UserRole.ADMIN)),
):
    result = await db.execute(
        select(Scan.latitude, Scan.longitude, Scan.compliance_status, Scan.store_name)
        .where(Scan.latitude.isnot(None), Scan.longitude.isnot(None))
    )
    points = []
    for row in result.all():
        points.append({
            "lat": row[0],
            "lng": row[1],
            "status": row[2].value if hasattr(row[2], 'value') else str(row[2]),
            "store": row[3],
        })
    return {"points": points}
