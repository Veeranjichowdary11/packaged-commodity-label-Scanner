import os
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from sqlalchemy import select, or_  # type: ignore # pyrefly: ignore
from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore # pyrefly: ignore
from typing import Optional

from app.core.database import get_db
from app.core.config import Settings
from app.models.models import User, Product, Scan
from app.schemas.schemas import ProductResponse, ScanResponse
from app.api.routes.auth import get_current_user
from app.services.report_generator import generate_report_number, generate_barcode_verification_pdf

settings = Settings()
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


import httpx


async def fetch_open_food_facts(barcode: str) -> Optional[dict]:
    """Query Open Food Facts public API for barcode metadata."""
    try:
        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(url, headers={"User-Agent": "PackagedCommodityScanner/1.0 (contact: support@janch.gov.in)"})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == 1:
                    p = data.get("product", {})
                    category = None
                    if p.get("categories"):
                        parts = [c.strip() for c in p["categories"].split(",") if c.strip()]
                        category = parts[0] if parts else None
                    return {
                        "name": p.get("product_name") or p.get("product_name_en") or p.get("generic_name"),
                        "brand": p.get("brands"),
                        "category": category,
                        "net_quantity": p.get("quantity"),
                        "image_url": p.get("image_front_url") or p.get("image_url"),
                        "ingredients": p.get("ingredients_text"),
                        "country_of_origin": p.get("countries") or "India",
                        "source": "Open Food Facts Global Registry",
                    }
    except Exception:
        pass
    return None


@router.get("/{barcode}/verify")
async def verify_against_database(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Step 1: Check local database
    result = await db.execute(select(Product).where(Product.barcode == barcode))
    product = result.scalar_one_or_none()

    # Step 2: If found in local database, run consistency checks
    if product:
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

        # Fetch extra metadata (like image) from Open Food Facts if available
        off_info = await fetch_open_food_facts(barcode)
        image_url = off_info.get("image_url") if off_info else None

        return {
            "found": True,
            "source": "local_database",
            "product": ProductResponse.model_validate(product),
            "image_url": image_url,
            "ingredients": off_info.get("ingredients") if off_info else None,
            "total_scans": len(recent_scans),
            "mismatches": mismatches,
            "is_consistent": len(mismatches) == 0,
            "alert": "POSSIBLE COUNTERFEIT - Label does not match database records" if mismatches else None,
            "message": "Product verified against Central Legal Metrology Database",
        }

    # Step 3: Product not in local database -> Query Open Food Facts global registry
    off_data = await fetch_open_food_facts(barcode)
    if off_data:
        # Cache product in local database for subsequent scans
        product = Product(
            barcode=barcode,
            name=off_data.get("name") or "Unspecified Product",
            brand=off_data.get("brand"),
            category=off_data.get("category"),
            net_quantity=off_data.get("net_quantity"),
            country_of_origin=off_data.get("country_of_origin"),
        )
        db.add(product)
        await db.commit()
        await db.refresh(product)

        return {
            "found": True,
            "source": "open_food_facts",
            "product": ProductResponse.model_validate(product),
            "image_url": off_data.get("image_url"),
            "ingredients": off_data.get("ingredients"),
            "total_scans": 0,
            "mismatches": [],
            "is_consistent": True,
            "alert": None,
            "message": "Product verified against Open Food Facts Global Registry",
        }

    # Step 4: Not found in either registry
    return {
        "found": False,
        "source": "none",
        "barcode": barcode,
        "message": "Product barcode not registered in local database or Open Food Facts. You can scan its label to register it.",
    }


@router.get("/{barcode}/report")
async def download_barcode_report(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    verification_data = await verify_against_database(barcode, db, user)
    if not verification_data.get("found"):
        raise HTTPException(status_code=404, detail="Barcode not found in registry")

    report_number = generate_report_number()
    pdf_path = await run_in_threadpool(
        generate_barcode_verification_pdf,
        barcode=barcode,
        product_data=verification_data,
        output_dir=settings.REPORTS_DIR,
        report_number=report_number,
        image_url=verification_data.get("image_url"),
    )

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="Failed to generate verification report")

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"barcode-verification-{barcode}.pdf",
    )

