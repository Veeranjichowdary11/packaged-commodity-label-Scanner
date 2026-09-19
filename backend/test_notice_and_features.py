import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.services.notice_generator import generate_rule32_notice
from app.core.config import Settings

settings = Settings()

def test_notice_generation():
    print("=== Testing Statutory Rule 32 Notice PDF Generation ===")
    sample_scan_data = {
        "scan_id": 101,
        "store_name": "Mega Mart Supermarket",
        "store_address": "Connaught Place, New Delhi - 110001",
        "barcode": "8901234567890",
        "inspector_name": "Rajesh Kumar",
    }
    sample_violations = [
        {
            "section_reference": "Rule 6(1)(e)",
            "rule_name": "Maximum Retail Price Overpricing",
            "description": "Package sold at Rs. 210.00 exceeding registered database MRP of Rs. 185.00.",
            "expected_value": "<= Rs. 185.00",
            "actual_value": "Rs. 210.00",
        },
        {
            "section_reference": "Rule 7 & 9",
            "rule_name": "Mandatory Font Size Non-Compliance",
            "description": "Net quantity numeral height is below the statutory minimum requirement of 4.0 mm.",
            "expected_value": ">= 4.0 mm",
            "actual_value": "1.8 mm",
        }
    ]
    sample_fields = {
        "common_name": "Premium Basmati Rice",
        "manufacturer": {"value": "Golden Harvest Foods Pvt Ltd, Delhi"},
        "net_quantity": {"value": 1.0, "unit": "kg"},
        "mrp": {"value": 210.0},
    }

    pdf_path = generate_rule32_notice(
        scan_data=sample_scan_data,
        violations=sample_violations,
        extracted_fields=sample_fields,
        output_dir=settings.REPORTS_DIR,
    )
    print(f"Generated Rule 32 Notice PDF: {pdf_path}")
    assert os.path.exists(pdf_path), "Notice PDF file was not created"
    assert os.path.getsize(pdf_path) > 1000, "Notice PDF file is too small"
    print(f"Notice PDF generated successfully! ({os.path.getsize(pdf_path)} bytes)")

if __name__ == "__main__":
    test_notice_generation()
