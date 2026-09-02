import re
from typing import Optional


def extract_mrp(text: str) -> Optional[dict]:
    patterns = [
        # Handle EasyOCR rendering ₹ as ? or other garbled chars
        r'(?:MRP|M\.R\.P\.?|Maximum\s+Retail\s+Price)\s*[:\.]?\s*(?:Rs\.?|₹|INR|[?])?\s*(\d+[\.,]?\d*)',
        r'(?:Rs\.?|₹|INR)\s*(\d+[\.,]?\d*)\s*(?:\(?\s*(?:incl|inclusive|including))',
        r'(?:price|MRP)\s*[:\s]*(\d+[\.,]?\d*)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(',', ''))
            has_tax_note = bool(re.search(
                r'incl.*?(?:tax|taxes)|inclusive.*?(?:tax|taxes)|all\s+taxes',
                text, re.IGNORECASE
            ))
            return {"value": value, "has_tax_note": has_tax_note, "raw": match.group(0)}
    return None


def extract_net_quantity(text: str) -> Optional[dict]:
    patterns = [
        r'(?:Net\s+(?:Wt\.?|Weight|Qty\.?|Quantity|Content))\s*[:\.]?\s*(\d+[\.,]?\d*)\s*(g|gm|gms|gram|grams|kg|kgs|kilogram|ml|mL|l|L|litre|liter|litres|liters|cm|mm|m|pieces?|pcs?|nos?|units?)',
        r'(\d+[\.,]?\d*)\s*(g|gm|gms|kg|kgs|ml|mL|l|L)\b',
    ]
    valid_units = {
        'g': 'g', 'gm': 'g', 'gms': 'g', 'gram': 'g', 'grams': 'g',
        'kg': 'kg', 'kgs': 'kg', 'kilogram': 'kg',
        'ml': 'ml', 'mL': 'ml',
        'l': 'L', 'L': 'L', 'litre': 'L', 'liter': 'L', 'litres': 'L', 'liters': 'L',
        'cm': 'cm', 'mm': 'mm', 'm': 'm',
        'piece': 'pcs', 'pieces': 'pcs', 'pcs': 'pcs', 'pc': 'pcs',
        'no': 'nos', 'nos': 'nos', 'unit': 'units', 'units': 'units',
    }
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(',', ''))
            raw_unit = match.group(2).strip().lower()
            std_unit = valid_units.get(raw_unit, raw_unit)
            return {"value": value, "unit": std_unit, "raw": match.group(0)}
    return None


def extract_manufacturer(text: str) -> Optional[dict]:
    # First try to find "Manufacturer/Packer" with explicit value after colon
    patterns = [
        r'(?:Manufacturer\s*/?\s*Packer)\s*[:\.]?\s*(.+?)(?:\n|(?:Date|Consumer|Country|Product\s+Name|Batch|FSSAI|Lic))',
        r'(?:Manufactured\s+by|Packed\s+by|Marketed\s+by|Imported\s+by)\s*[:\.]?\s*(.+?)(?:\n|(?:Date|Consumer|Country|Product\s+Name|Batch|FSSAI|Lic|MRP|Net))',
        r'(?:Mfg\.?\s+by|Packer|Marketer|Importer)\s*[:\.]?\s*(.+?)(?:\n|(?:Date|Consumer|Country|Product\s+Name|Batch|FSSAI|Lic|MRP|Net))',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            addr = match.group(1).strip().rstrip(',.- ')
            if len(addr) > 10:
                nearby_text = text[max(0, match.start() - 50):min(len(text), match.end() + 350)]
                has_pincode = bool(re.search(r'\b\d{6}\b', addr) or re.search(r'\b\d{6}\b', nearby_text))
                return {"value": addr, "has_pincode": has_pincode, "raw": match.group(0)}

    # Fallback: scan lines for manufacturer keywords (but NOT "Mfg/Packaging" which is a date field)
    lines = text.split('\n')
    for i, line in enumerate(lines):
        # Skip lines that are actually date references
        if re.search(r'Mfg\s*/?\s*Packag', line, re.IGNORECASE):
            continue
        if re.search(r'(?:Manufactured|Packed|Packer|Marketed|Imported|Mfd|Pkg)', line, re.IGNORECASE):
            addr_lines = [line]
            for j in range(i + 1, min(i + 6, len(lines))):
                if re.search(r'^(MRP|M\.R\.P|Net\s+Qty|Best\s+Before|Expiry|Exp\b|Date\s+of|Batch\b|Ingredients)', lines[j], re.IGNORECASE):
                    break
                addr_lines.append(lines[j])
            addr = ' '.join(addr_lines).strip()
            if len(addr) > 10:
                # Also check surrounding lines (within 6 lines) for a 6-digit pin code
                nearby_text = ' '.join(lines[max(0, i-1):min(i+7, len(lines))])
                has_pincode = bool(re.search(r'\b\d{6}\b', nearby_text))
                return {"value": addr, "has_pincode": has_pincode, "raw": addr}

    # Fallback 2: Look for lines with 6-digit pincode or address keywords (e.g. Plot No, Sector, Pvt Ltd)
    for i, line in enumerate(lines):
        if re.search(r'\b\d{6}\b', line) or re.search(r'\b(?:Plot\s+No|Sector|Pvt|Ltd|Limited)\b', line, re.IGNORECASE):
            start_idx = max(0, i - 1) if i > 0 and not re.search(r'(MRP|Net|Date|FSSAI|Lic|Consumer|Country|Product)', lines[i-1], re.IGNORECASE) else i
            addr_lines = []
            for j in range(start_idx, min(i + 4, len(lines))):
                if re.search(r'^(MRP|Net|Best|Exp|Date\s+of|Batch|Consumer|Country|Product\s+Name|INGREDIENTS)', lines[j], re.IGNORECASE):
                    break
                addr_lines.append(lines[j])
            addr = ' '.join(addr_lines).strip()
            if len(addr) > 10:
                nearby_text = ' '.join(lines[max(0, i-1):min(i+5, len(lines))])
                has_pincode = bool(re.search(r'\b\d{6}\b', nearby_text))
                return {"value": addr, "has_pincode": has_pincode, "raw": addr}

    return None


def extract_date_info(text: str) -> Optional[dict]:
    result = {}
    mfg_patterns = [
        r'(?:Date\s+of\s+Mfg\s*/?\s*Packag(?:ing|e))\s*[:\.]?\s*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4})',
        r'(?:Mfg\.?\s*(?:Date|Dt\.?)?|Date\s+of\s+(?:Mfg|Manufacture|Manufacturing|Packing|Pkg))\s*[:\.]?\s*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}|\d{1,2}[\/-]\d{2,4}|[A-Za-z]+[\s,]*\d{2,4})',
        r'(?:Mfg|MFD|PKD|PKG)\s*[:\.]?\s*(\d{1,2}[\/-]\d{2,4}|[A-Za-z]{3,}\s*[\/-]?\s*\d{2,4})',
    ]
    exp_patterns = [
        r'(?:Exp(?:iry)?\.?\s*(?:Date|Dt\.?)?|Best\s+Before|Use\s+Before|Use\s+By|BB)\s*[:\.]?\s*(\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}|\d{1,2}[\/-]\d{2,4}|[A-Za-z]+[\s,]*\d{2,4}|\d+\s*(?:months?|days?|years?))',
    ]
    for pattern in mfg_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["manufacture_date"] = {"value": match.group(1).strip(), "raw": match.group(0)}
            break
    for pattern in exp_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["expiry_date"] = {"value": match.group(1).strip(), "raw": match.group(0)}
            break
    return result if result else None


def extract_consumer_care(text: str) -> Optional[dict]:
    result = {}
    phone = re.search(r'(?:Consumer\s*Care|Customer\s*Care|Helpline|Toll\s*Free|Contact|Call(?:\s+Us)?(?:\s+At)?)\s*[:\.]?\s*[\+]?[\d\s\-]{7,15}', text, re.IGNORECASE)
    if phone:
        result["phone"] = phone.group(0).strip()
    email = re.search(r'[\w\.\-]+@[\w\.\-]+\.\w+', text)
    if email:
        result["email"] = email.group(0).strip()
    if not result.get("phone"):
        phone_only = re.search(r'(?:1800|1860)[\s\-]?(?:\d{2,4}[\s\-]?\d{3,4}|\d{6,7})', text)
        if phone_only:
            result["phone"] = phone_only.group(0).strip()
    feedback_match = re.search(r'(?:Consumer\s*(?:Services\s*)?Manager|Feedback\s*(?:or\s*)?Queries|Write\s+to\s*:)', text, re.IGNORECASE)
    if feedback_match and not result.get("details"):
        result["details"] = "Consumer services contact present on package"
    return result if result else None


def extract_country_of_origin(text: str) -> Optional[str]:
    patterns = [
        r'(?:Country\s+of\s+Origin|Made\s+in|Product\s+of|Origin)\s*[:\.]?\s*([A-Za-z\s]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_common_name(text: str) -> Optional[str]:
    """Extract product name — prefer explicit 'Product Name' field over first line."""
    # First try explicit "Product Name" label (common on Indian FMCG products)
    product_name_match = re.search(
        r'(?:Product\s+Name|Name\s+of\s+(?:the\s+)?(?:Product|Commodity|Food))\s*[:\.]?\s*(.+?)(?:\n|$)',
        text, re.IGNORECASE
    )
    if product_name_match:
        name = product_name_match.group(1).strip()
        if len(name) > 2:
            return name

    # Next check for common FMCG product categories
    prod_pattern = r'\b(Potato\s+Chips|Chips|Biscuits|Cookies|Namkeen|Noodles|Snacks|Tea|Coffee|Chocolate|Atta|Wheat\s+Flour|Rice|Cooking\s+Oil|Edible\s+Oil|Spices?|Masala)\b'
    if re.search(prod_pattern, text, re.IGNORECASE):
        for line in text.split('\n'):
            line_clean = line.strip().strip('"\'')
            m = re.search(prod_pattern, line_clean, re.IGNORECASE)
            if m and len(line_clean.split()) <= 6:
                if len(line_clean.split()) > 3:
                    return m.group(1).title()
                return line_clean.title()

    # Fallback: use first non-numeric, non-MRP, non-nutritional line
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or len(line) < 3:
            continue
        # Skip lines that are clearly field labels/values or nutritional facts
        if re.match(r'^(MRP|M\.R\.P|Net|Date|Batch|FSSAI|Lic|Consumer|Country|Manufacturer|Ingredients|Nutri|Energy|Protein|Fat|Carb|Sugar|Sodium|Approx|Values|Per|Serving|IMUTR)', line, re.IGNORECASE):
            continue
        if re.search(r'\b(kcal|kJ|mcg|mg)\b', line, re.IGNORECASE):
            continue
        if re.search(r'\d', line) and len(line.split()) <= 2:
            continue
        if re.match(r'^[\d\s\W]+$', line):
            continue
        if len(line.split()) > 7:
            continue
        return line

    return None


def extract_batch_number(text: str) -> Optional[str]:
    """Extract batch/lot number — handle 'Batch Number' as a two-word label."""
    patterns = [
        # "Batch Number : B5120524A1" or "Batch Number B5120524A1"
        r'(?:Batch\s+(?:No\.?|Number)|Lot\s+(?:No\.?|Number))\s*[:\.]?\s*([A-Za-z0-9][\w\-\/]+)',
        # "B. No. XYZ" or "L. No. XYZ"
        r'(?:B\.?\s*No\.?|L\.?\s*No\.?)\s*[:\.]?\s*([A-Za-z0-9][\w\-\/]+)',
        # Simple "Batch: XYZ" (only if followed by an alphanumeric batch code, not "Number")
        r'(?:Batch|Lot)\s*[:\.]?\s*(?!Number|No)([A-Za-z0-9][\w\-\/]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            # Sanity check: batch numbers are typically 4+ chars
            if len(val) >= 4:
                return val
    return None


def extract_fssai(text: str) -> Optional[str]:
    match = re.search(r'(?:FSSAI|Lic\.?\s*No\.?|License\s*No\.?)\s*[:\.]?\s*(\d{14})', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    fssai_only = re.search(r'\b(\d{14})\b', text)
    if fssai_only:
        return fssai_only.group(1).strip()
    return None


def extract_all_fields(text: str) -> dict:
    fields = {}
    mrp = extract_mrp(text)
    if mrp:
        fields["mrp"] = mrp

    net_qty = extract_net_quantity(text)
    if net_qty:
        fields["net_quantity"] = net_qty

    manufacturer = extract_manufacturer(text)
    if manufacturer:
        fields["manufacturer"] = manufacturer

    dates = extract_date_info(text)
    if dates:
        fields["dates"] = dates

    consumer_care = extract_consumer_care(text)
    if consumer_care:
        fields["consumer_care"] = consumer_care

    country = extract_country_of_origin(text)
    if country:
        fields["country_of_origin"] = country

    common_name = extract_common_name(text)
    if common_name:
        fields["common_name"] = common_name

    batch = extract_batch_number(text)
    if batch:
        fields["batch_number"] = batch

    fssai = extract_fssai(text)
    if fssai:
        fields["fssai_license"] = fssai

    return fields
