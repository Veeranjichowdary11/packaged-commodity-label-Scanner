"""Seed script to populate demo data for hackathon presentation."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import engine, async_session, Base
from app.core.security import hash_password
from app.models.models import (
    User, UserRole, Product, Scan, Violation,
    ComplianceStatus, ViolationSeverity
)
from datetime import datetime, timezone, timedelta
import random


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        admin = User(
            email="admin@janch.in", username="admin",
            hashed_password=hash_password("admin123"),
            full_name="System Admin", role=UserRole.ADMIN,
            organization="Dept. of Consumer Affairs"
        )
        inspector = User(
            email="inspector@janch.in", username="inspector",
            hashed_password=hash_password("inspector123"),
            full_name="Rajesh Kumar", role=UserRole.INSPECTOR,
            organization="Legal Metrology, Delhi"
        )
        consumer = User(
            email="consumer@janch.in", username="consumer",
            hashed_password=hash_password("consumer123"),
            full_name="Priya Sharma", role=UserRole.CONSUMER,
        )
        manufacturer = User(
            email="mfg@janch.in", username="manufacturer",
            hashed_password=hash_password("mfg123"),
            full_name="Amit Patel", role=UserRole.MANUFACTURER,
            organization="Patel Foods Pvt Ltd"
        )
        db.add_all([admin, inspector, consumer, manufacturer])
        await db.flush()

        products_data = [
            {"barcode": "8901234567890", "name": "Premium Basmati Rice", "brand": "Golden Harvest", "category": "Food Grains", "manufacturer_name": "Golden Harvest Foods Ltd", "net_quantity": "1 kg", "mrp": 185.0, "country_of_origin": "India"},
            {"barcode": "8905678901234", "name": "Refined Sunflower Oil", "brand": "Fortune", "category": "Edible Oil", "manufacturer_name": "Adani Wilmar Ltd", "net_quantity": "1 L", "mrp": 155.0, "country_of_origin": "India"},
            {"barcode": "8902345678901", "name": "Digestive Biscuits", "brand": "Britannia", "category": "Biscuits", "manufacturer_name": "Britannia Industries Ltd", "net_quantity": "250 g", "mrp": 45.0, "country_of_origin": "India"},
            {"barcode": "8903456789012", "name": "Instant Noodles", "brand": "Maggi", "category": "Instant Food", "manufacturer_name": "Nestle India Ltd", "net_quantity": "70 g", "mrp": 14.0, "country_of_origin": "India"},
            {"barcode": "8904567890123", "name": "Washing Powder", "brand": "Surf Excel", "category": "Detergent", "manufacturer_name": "Hindustan Unilever Ltd", "net_quantity": "500 g", "mrp": 120.0, "country_of_origin": "India"},
        ]
        products = []
        for p in products_data:
            product = Product(**p)
            db.add(product)
            products.append(product)
        await db.flush()

        scan_types = ["manual", "live_camera", "crowdsource"]
        statuses = [ComplianceStatus.COMPLIANT, ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIALLY_COMPLIANT]
        locations = [
            (28.6139, 77.2090, "Big Bazaar", "Connaught Place, Delhi"),
            (19.0760, 72.8777, "DMart", "Andheri West, Mumbai"),
            (12.9716, 77.5946, "Reliance Fresh", "Koramangala, Bangalore"),
            (22.5726, 88.3639, "Spencer's", "Park Street, Kolkata"),
            (13.0827, 80.2707, "StarBazaar", "T Nagar, Chennai"),
        ]

        violation_templates = [
            {"rule_code": "LM-R6-MRP-TAX", "rule_name": "MRP - Inclusive of All Taxes", "severity": ViolationSeverity.MAJOR, "section_reference": "Rule 6(1)(e)"},
            {"rule_code": "LM-R6-MFG-PIN", "rule_name": "Manufacturer Address - Pin Code", "severity": ViolationSeverity.MAJOR, "section_reference": "Rule 6(1)(c)"},
            {"rule_code": "LM-R6-CARE", "rule_name": "Consumer Care Details", "severity": ViolationSeverity.MAJOR, "section_reference": "Rule 6(1)(g)"},
            {"rule_code": "LM-R6-DATE", "rule_name": "Month and Year of Manufacture", "severity": ViolationSeverity.CRITICAL, "section_reference": "Rule 6(1)(d)"},
            {"rule_code": "LM-R6-NETQTY", "rule_name": "Net Quantity Declaration", "severity": ViolationSeverity.CRITICAL, "section_reference": "Rule 6(1)(b)"},
        ]

        for i in range(25):
            product = random.choice(products)
            loc = random.choice(locations)
            status = random.choice(statuses)
            st = random.choice(scan_types)
            score = 100.0 if status == ComplianceStatus.COMPLIANT else (random.uniform(50, 85) if status == ComplianceStatus.PARTIALLY_COMPLIANT else random.uniform(10, 50))
            days_ago = random.randint(0, 30)

            scan = Scan(
                user_id=random.choice([inspector.id, consumer.id]),
                product_id=product.id,
                image_path="uploads/demo_placeholder.jpg",
                scan_type=st,
                latitude=loc[0] + random.uniform(-0.01, 0.01),
                longitude=loc[1] + random.uniform(-0.01, 0.01),
                store_name=loc[2],
                store_address=loc[3],
                raw_ocr_text=f"Demo OCR text for {product.name}",
                extracted_fields={"mrp": {"value": product.mrp, "has_tax_note": status == ComplianceStatus.COMPLIANT}},
                barcode_detected=product.barcode,
                compliance_status=status,
                compliance_score=round(score, 1),
                total_checks=9,
                passed_checks=9 if status == ComplianceStatus.COMPLIANT else random.randint(3, 7),
                failed_checks=0 if status == ComplianceStatus.COMPLIANT else random.randint(2, 6),
                created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
            )
            db.add(scan)
            await db.flush()

            if status != ComplianceStatus.COMPLIANT:
                num_violations = random.randint(1, 3)
                chosen = random.sample(violation_templates, min(num_violations, len(violation_templates)))
                for vt in chosen:
                    violation = Violation(
                        scan_id=scan.id,
                        rule_code=vt["rule_code"],
                        rule_name=vt["rule_name"],
                        description=f"MISSING: {vt['rule_name']} not found on product label.",
                        severity=vt["severity"],
                        field_name=vt["rule_code"].split("-")[-1].lower(),
                        expected_value="Present on label",
                        actual_value="Not found",
                        section_reference=vt["section_reference"],
                    )
                    db.add(violation)

        await db.commit()
        print("Seed data created successfully!")
        print("Demo accounts:")
        print("  Admin:        admin@janch.in / admin123")
        print("  Inspector:    inspector@janch.in / inspector123")
        print("  Consumer:     consumer@janch.in / consumer123")
        print("  Manufacturer: mfg@janch.in / mfg123")


if __name__ == "__main__":
    asyncio.run(seed())
