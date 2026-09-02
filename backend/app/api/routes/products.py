from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_  # type: ignore # pyrefly: ignore
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore # pyrefly: ignore
from typing import Optional

from app.core.database import get_db
from app.models.models import User, Product, Scan
from app.schemas.schemas import ProductResponse, ScanResponse
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=list[ProductResponse])
@router.get("", response_model=list[ProductResponse])
async def search_products(
    q: Optional[str] = Query(None, description="Search by name, brand or barcode"),
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = select(Product).order_by(Product.created_at.desc())
    if q:
        query = query.where(
            or_(
                Product.name.ilike(f"%{q}%"),
                Product.brand.ilike(f"%{q}%"),
                Product.barcode.ilike(f"%{q}%"),
                Product.manufacturer_name.ilike(f"%{q}%"),
            )
        )
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()
    return [ProductResponse.model_validate(p) for p in products]


@router.get("/{barcode}", response_model=ProductResponse)
async def get_product_by_barcode(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Product).where(Product.barcode == barcode))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)


@router.get("/{barcode}/verify")
async def verify_against_database(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Product).where(Product.barcode == barcode))
    product = result.scalar_one_or_none()
    if not product:
        return {"found": False, "message": "Product not in database. First scan will create an entry."}

    scan_result = await db.execute(
        select(Scan)
        .where(Scan.product_id == product.id)
        .order_by(Scan.created_at.desc())
        .limit(5)
    )
    recent_scans = scan_result.scalars().all()

    mismatches = []
    for scan in recent_scans:
        fields = scan.extracted_fields or {}
        mrp_field = fields.get("mrp", {})
        scan_mrp = mrp_field.get("value") if isinstance(mrp_field, dict) else None
        if scan_mrp and product.mrp and abs(scan_mrp - product.mrp) > 0.01:
            mismatches.append({
                "scan_id": scan.id,
                "field": "mrp",
                "expected": product.mrp,
                "found": scan_mrp,
                "date": str(scan.created_at),
            })

        mfg_field = fields.get("manufacturer", {})
        scan_mfg = mfg_field.get("value") if isinstance(mfg_field, dict) else None
        if scan_mfg and product.manufacturer_name:
            if product.manufacturer_name.lower() not in scan_mfg.lower():
                mismatches.append({
                    "scan_id": scan.id,
                    "field": "manufacturer",
                    "expected": product.manufacturer_name,
                    "found": scan_mfg,
                    "date": str(scan.created_at),
                })

    return {
        "found": True,
        "product": ProductResponse.model_validate(product),
        "total_scans": len(recent_scans),
        "mismatches": mismatches,
        "is_consistent": len(mismatches) == 0,
        "alert": "POSSIBLE COUNTERFEIT - Label does not match database records" if mismatches else None,
    }
