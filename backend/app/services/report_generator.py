import hashlib
import json
import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_report_number() -> str:
    now = datetime.now(timezone.utc)
    return f"JNC-{now.strftime('%Y%m%d%H%M%S')}-{os.urandom(3).hex().upper()}"


def compute_hash(scan_data: dict, previous_hash: str = "") -> str:
    payload = json.dumps(scan_data, sort_keys=True, default=str) + previous_hash
    return hashlib.sha256(payload.encode()).hexdigest()


def generate_pdf_report(
    scan_data: dict,
    violations: list,
    extracted_fields: dict,
    image_path: str,
    output_dir: str,
    report_number: str,
) -> str:
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"{report_number}.pdf")

    doc = SimpleDocTemplate(pdf_path, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, textColor=colors.HexColor('#1a365d'))
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=13, textColor=colors.HexColor('#2d3748'), spaceAfter=6)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=4)

    elements.append(Paragraph("Packaged Commodity Label Scanner - Inspection Report", title_style))
    elements.append(Paragraph("Legal Metrology (Packaged Commodities) Rules, 2011", ParagraphStyle('Sub', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, textColor=colors.grey)))
    elements.append(Spacer(1, 8*mm))

    meta_data = [
        ["Report Number:", report_number],
        ["Date:", datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")],
        ["Scan Type:", scan_data.get("scan_type", "Manual")],
        ["Compliance Status:", scan_data.get("compliance_status", "Pending").upper()],
        ["Score:", f"{scan_data.get('compliance_score', 0)}%"],
    ]
    if scan_data.get("store_name"):
        meta_data.append(["Store:", scan_data["store_name"]])
    if scan_data.get("latitude") and scan_data.get("longitude"):
        meta_data.append(["Location:", f"{scan_data['latitude']}, {scan_data['longitude']}"])

    meta_table = Table(meta_data, colWidths=[4*cm, 12*cm])
    meta_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 6*mm))

    if image_path and os.path.exists(image_path):
        elements.append(Paragraph("Product Image", header_style))
        try:
            from PIL import Image as PILImage
            with PILImage.open(image_path) as test_img:
                test_img.verify()
            img = RLImage(image_path, width=8*cm, height=8*cm, kind='proportional')
            elements.append(img)
        except Exception:
            elements.append(Paragraph("[Image could not be loaded]", body_style))
        elements.append(Spacer(1, 6*mm))

    def format_field_display(field_key: str, val: any) -> str:
        if val is None:
            return "NOT FOUND"
        if field_key == "mrp":
            if isinstance(val, dict):
                v = val.get("value")
                if v is not None:
                    note = " (incl. of all taxes)" if val.get("has_tax_note") else ""
                    return f"Rs. {v:.2f}{note}"
                return str(val.get("raw", val))
            return str(val)
        elif field_key == "dates":
            if isinstance(val, dict):
                parts = []
                if "manufacture_date" in val:
                    mfg = val["manufacture_date"].get("value", "") if isinstance(val["manufacture_date"], dict) else str(val["manufacture_date"])
                    if mfg:
                        parts.append(f"Mfg: {mfg}")
                if "expiry_date" in val:
                    exp = val["expiry_date"].get("value", "") if isinstance(val["expiry_date"], dict) else str(val["expiry_date"])
                    if exp:
                        parts.append(f"Exp: {exp}")
                if parts:
                    return " | ".join(parts)
                return str(val.get("raw", val.get("value", val)))
            return str(val)
        elif field_key == "consumer_care":
            if isinstance(val, dict):
                parts = []
                if val.get("phone"):
                    parts.append(f"Tel: {val['phone']}")
                if val.get("email"):
                    parts.append(f"Email: {val['email']}")
                if not parts and val.get("details"):
                    parts.append(val["details"])
                if parts:
                    return ", ".join(parts)
                return str(val.get("raw", val.get("value", val)))
            return str(val)
        elif field_key == "net_quantity":
            if isinstance(val, dict):
                v = val.get("value")
                u = val.get("unit", "")
                if v is not None:
                    return f"{v:g} {u}".strip()
                return str(val.get("raw", val))
            return str(val)
        elif field_key == "manufacturer":
            if isinstance(val, dict):
                return str(val.get("value", val.get("raw", val)))
            return str(val)
        elif isinstance(val, dict):
            return str(val.get("value", val.get("raw", val)))
        return str(val)

    elements.append(Paragraph("Extracted Declarations", header_style))
    field_rows = [["Field", "Value", "Status"]]
    field_labels = {
        "mrp": "MRP",
        "net_quantity": "Net Quantity",
        "manufacturer": "Manufacturer/Packer",
        "dates": "Date of Mfg/Packing",
        "consumer_care": "Consumer Care",
        "country_of_origin": "Country of Origin",
        "common_name": "Product Name",
        "batch_number": "Batch Number",
        "fssai_license": "FSSAI License",
    }
    violated_fields = {v["field_name"] for v in violations}
    cell_style = ParagraphStyle('TableCell', parent=styles['Normal'], fontSize=8.5, leading=11)

    for key, label in field_labels.items():
        val = extracted_fields.get(key)
        if val is None:
            display_text = "NOT FOUND"
            status = "MISSING" if key in violated_fields else "N/A"
        else:
            display_text = format_field_display(key, val)
            status = "VIOLATION" if key in violated_fields else "OK"

        val_flowable = Paragraph(display_text, cell_style)
        field_rows.append([label, val_flowable, status])

    field_table = Table(field_rows, colWidths=[4*cm, 8.5*cm, 3.5*cm])
    status_colors = {"OK": colors.HexColor('#38a169'), "MISSING": colors.HexColor('#e53e3e'), "VIOLATION": colors.HexColor('#dd6b20'), "N/A": colors.grey}
    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    for i, row in enumerate(field_rows[1:], 1):
        status = row[2]
        color = status_colors.get(status, colors.black)
        table_style.append(('TEXTCOLOR', (2, i), (2, i), color))
        table_style.append(('FONTNAME', (2, i), (2, i), 'Helvetica-Bold'))

    field_table.setStyle(TableStyle(table_style))
    elements.append(field_table)
    elements.append(Spacer(1, 6*mm))

    if violations:
        elements.append(Paragraph("Violations Found", header_style))
        for i, v in enumerate(violations, 1):
            sev_color = {"critical": "#e53e3e", "major": "#dd6b20", "minor": "#d69e2e", "info": "#3182ce"}.get(v.get("severity", ""), "#333")
            elements.append(Paragraph(
                f'<b>{i}. [{v.get("severity", "").upper()}]</b> {v["rule_name"]} '
                f'<font color="grey">(Section {v.get("section_reference", "N/A")})</font>',
                ParagraphStyle('VTitle', parent=body_style, textColor=colors.HexColor(sev_color), fontSize=10)
            ))
            elements.append(Paragraph(v["description"], body_style))
            if v.get("expected_value"):
                elements.append(Paragraph(f'<b>Expected:</b> {v["expected_value"]}', body_style))
            if v.get("actual_value"):
                elements.append(Paragraph(f'<b>Found:</b> {v["actual_value"]}', body_style))
            elements.append(Spacer(1, 3*mm))
    else:
        elements.append(Paragraph("No Violations Found - Product is Fully Compliant", ParagraphStyle('Pass', parent=header_style, textColor=colors.HexColor('#38a169'))))

    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(
        f'<font size="8" color="grey">Report hash: {compute_hash(scan_data)} | Generated by Janch Compliance System</font>',
        ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER)
    ))

    doc.build(elements)
    return pdf_path
