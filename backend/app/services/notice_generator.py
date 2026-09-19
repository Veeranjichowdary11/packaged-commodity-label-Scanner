import os
import hashlib
from datetime import datetime, timezone, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT


def generate_rule32_notice(
    scan_data: dict,
    violations: list,
    extracted_fields: dict,
    output_dir: str,
    notice_number: str = "",
) -> str:
    """
    Generate an official Statutory Show Cause Notice under Rule 32 of the
    Legal Metrology (Packaged Commodities) Rules, 2011 and Section 18 / 36
    of the Legal Metrology Act, 2009.
    """
    os.makedirs(output_dir, exist_ok=True)
    if not notice_number:
        now = datetime.now(timezone.utc)
        notice_number = f"LM/ENF/SCN/{now.strftime('%Y%m%d')}/{os.urandom(2).hex().upper()}"

    pdf_path = os.path.join(output_dir, f"{notice_number.replace('/', '_')}.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    styles = getSampleStyleSheet()
    elements = []

    # Custom styles
    govt_title = ParagraphStyle(
        'GovtTitle',
        parent=styles['Normal'],
        fontSize=13,
        leading=16,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#1a202c')
    )
    dept_subtitle = ParagraphStyle(
        'DeptSub',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#4a5568')
    )
    notice_heading = ParagraphStyle(
        'NoticeHeading',
        parent=styles['Normal'],
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#9b2c2c'),
        spaceBefore=8,
        spaceAfter=10
    )
    body_justified = ParagraphStyle(
        'BodyJustified',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor('#2d3748'),
        spaceAfter=6
    )
    legal_ref_style = ParagraphStyle(
        'LegalRef',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1a365d'),
        fontName='Helvetica-Bold'
    )

    # 1. Government Header
    elements.append(Paragraph("GOVERNMENT OF INDIA", govt_title))
    elements.append(Paragraph("MINISTRY OF CONSUMER AFFAIRS, FOOD & PUBLIC DISTRIBUTION", govt_title))
    elements.append(Paragraph("DEPARTMENT OF CONSUMER AFFAIRS — LEGAL METROLOGY DIVISION", dept_subtitle))
    elements.append(Paragraph("OFFICE OF THE CONTROLLER OF LEGAL METROLOGY", dept_subtitle))
    elements.append(Spacer(1, 3 * mm))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1a365d'), spaceAfter=8))

    # 2. Reference & Date Line
    now_str = datetime.now(timezone.utc).strftime("%d %B %Y")
    ref_table = Table([
        [Paragraph(f"<b>Notice No:</b> {notice_number}", styles['Normal']),
         Paragraph(f"<b>Date of Issue:</b> {now_str}", ParagraphStyle('RDate', parent=styles['Normal'], alignment=TA_RIGHT))]
    ], colWidths=[10 * cm, 7.5 * cm])
    ref_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(ref_table)
    elements.append(Spacer(1, 4 * mm))

    # 3. Addressee (Violator / Manufacturer / Retailer)
    mfg_info = extracted_fields.get("manufacturer") or {}
    mfg_name = mfg_info.get("value") if isinstance(mfg_info, dict) else str(mfg_info or "The Designated Packer / Manufacturer")
    store_name = scan_data.get("store_name") or "Retail Establishment"
    store_addr = scan_data.get("store_address") or "Inspection Location"

    addressee_text = (
        f"<b>TO:</b><br/>"
        f"<b>1. M/s {mfg_name}</b> (Manufacturer / Packer / Brand Owner)<br/>"
        f"<b>2. M/s {store_name}</b>, {store_addr} (Retailer / Person in Possession)"
    )
    elements.append(Paragraph(addressee_text, styles['Normal']))
    elements.append(Spacer(1, 4 * mm))

    # 4. Notice Subject & Heading
    elements.append(Paragraph("STATUTORY SHOW-CAUSE NOTICE UNDER RULE 32", notice_heading))
    elements.append(Paragraph(
        "<b>SUBJECT:</b> Notice for Contravention of the Legal Metrology (Packaged Commodities) Rules, 2011 "
        "read with Sections 18 and 36 of the Legal Metrology Act, 2009 regarding non-compliant packaging declarations.",
        legal_ref_style
    ))
    elements.append(Spacer(1, 4 * mm))

    # 5. Body Preamble
    preamble = (
        "WHEREAS, during an official inspection conducted by the authorized Legal Metrology Inspector on "
        f"<b>{now_str}</b> at the premises of M/s {store_name}, packages of the commodity detailed hereunder were "
        "examined for statutory compliance under the provisions of the Legal Metrology (Packaged Commodities) Rules, 2011."
    )
    elements.append(Paragraph(preamble, body_justified))

    prod_name = extracted_fields.get("common_name") or "Packaged Commodity"
    barcode_val = scan_data.get("barcode") or "N/A"
    mrp_val = extracted_fields.get("mrp")
    mrp_str = f"Rs. {mrp_val.get('value'):.2f}" if isinstance(mrp_val, dict) and mrp_val.get('value') else "Not Declared / Non-standard"
    net_qty_val = extracted_fields.get("net_quantity")
    net_qty_str = f"{net_qty_val.get('value')} {net_qty_val.get('unit')}" if isinstance(net_qty_val, dict) else "Not Declared"

    prod_summary = [
        ["Product / Commodity Name:", prod_name],
        ["Barcode (GTIN):", barcode_val],
        ["Declared Net Quantity:", net_qty_str],
        ["Declared Retail Price (MRP):", mrp_str],
        ["Scan Reference ID:", f"SCN-SCAN-{scan_data.get('scan_id', '001')}"],
    ]
    p_table = Table(prod_summary, colWidths=[6 * cm, 11.5 * cm])
    p_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    elements.append(p_table)
    elements.append(Spacer(1, 4 * mm))

    # 6. Schedule of Contraventions & Violations
    elements.append(Paragraph(
        "AND WHEREAS, upon physical inspection and verification against the central statutory standards, "
        "the following specific contraventions of law have been recorded:",
        body_justified
    ))

    v_rows = [["Sl.", "Statutory Provision", "Nature of Contravention", "Legal Consequence"]]
    for idx, v in enumerate(violations, 1):
        v_rows.append([
            str(idx),
            Paragraph(f"<b>{v.get('section_reference', 'Rule 6')}</b><br/>{v.get('rule_name', '')}", styles['Normal']),
            Paragraph(f"{v.get('description', '')}<br/><b>Expected:</b> {v.get('expected_value', '-')}<br/><b>Found:</b> {v.get('actual_value', '-')}", styles['Normal']),
            Paragraph("Offence punishable under Sec 36(1) of LM Act, 2009", styles['Normal']),
        ])

    if len(v_rows) == 1:
        v_rows.append(["1", "Rule 7 / 9", "Statutory Font Size & Legibility Verification Required", "Verification pending"])

    v_table = Table(v_rows, colWidths=[1 * cm, 4.5 * cm, 7.5 * cm, 4.5 * cm])
    v_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#742a2a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(v_table)
    elements.append(Spacer(1, 4 * mm))

    # 7. Directive & Show-Cause Mandate
    deadline_date = (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%d %B %Y")
    directive = (
        f"NOW THEREFORE, you are hereby called upon to <b>SHOW CAUSE</b> within <b>15 (fifteen) days</b> "
        f"from the receipt of this notice (i.e. on or before <b>{deadline_date}</b>), as to why prosecution "
        "proceedings should not be initiated against you under <b>Section 36 of the Legal Metrology Act, 2009</b> "
        "(punishable with fine up to <b>Rs. 25,000/-</b> for first offence, <b>Rs. 50,000/-</b> for second offence, "
        "and imprisonment for subsequent offences).<br/><br/>"
        "You are further afforded an opportunity to apply for <b>Compounding of Offence</b> under Section 48 "
        "of the Act by depositing the prescribed compounding fees, failing which legal proceedings in the competent "
        "Court of Law shall be instituted without further notice."
    )
    elements.append(Paragraph(directive, body_justified))
    elements.append(Spacer(1, 5 * mm))

    # 8. Signature Block
    insp_name = scan_data.get("inspector_name") or "Authorized Inspector"
    sig_block = [
        ["", Paragraph(f"<b>Issued by:</b><br/><b>{insp_name}</b><br/>Inspector of Legal Metrology<br/>Enforcement & Standards Division<br/>Dept. of Consumer Affairs", styles['Normal'])]
    ]
    sig_table = Table(sig_block, colWidths=[10 * cm, 7.5 * cm])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(sig_table)
    elements.append(Spacer(1, 6 * mm))

    # 9. Security Hash Footer
    sec_hash = hashlib.sha256(f"{notice_number}:{barcode_val}:{now_str}".encode()).hexdigest()
    elements.append(Paragraph(
        f"<font size='7' color='grey'>Statutory Notice Hash: {sec_hash} | Digitally generated via Janch National Portal</font>",
        ParagraphStyle('Foot', parent=styles['Normal'], alignment=TA_CENTER)
    ))

    doc.build(elements)
    return pdf_path
