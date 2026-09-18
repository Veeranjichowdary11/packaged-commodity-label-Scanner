import re
from typing import Optional


def extract_mrp(text: str) -> Optional[dict]:
    # Handle EasyOCR rendering ₹ or : as {, ?, [, (, <, ~, etc., or standard Rs./INR/₹
    patterns = [
        r'(?:MRP|M\.R\.P\.?|Maximum\s+Retail\s+Price|Retail\s+Price)\s*[:\.\-]?\s*(?:Rs\.?|₹|INR|[?{\[\(<\|~/\\*#])*\s*(\d+[\.,]\d{1,2}|\d+)',
        r'(?:Rs\.?|₹|INR|[?{\[])\s*(\d+[\.,]?\d*)\s*(?:\(?\s*(?:incl|inclusive|including))',
        r'(?:price|MRP)\s*[:\s\-]*[?{\[\(<\|~/\\*#]?\s*(\d+[\.,]\d{1,2}|\d+)',
    ]
    has_tax_note = bool(re.search(
        r'incl.*?(?:tax|taxes)|inclusive.*?(?:tax|taxes)|all\s+taxes',
        text, re.IGNORECASE
    ))

    # Look for Unit Sale Price (USP / E#P), e.g. "USP 0.07/ml" (mandatory in Legal Metrology)
    usp_m = re.search(r'(?:USP|E#P|Unit\s+Sale\s+Price)\s*[:\.\-,\s]*[?{\[\(<\|~/\\*#]?\s*(?:Rs\.?|₹)?\s*(\d+[\.,]\d{1,4})\s*(?:\/|\s+per\s+)?(ml|g|kg|l|fl)', text, re.IGNORECASE)
    if usp_m:
        try:
            usp_val = float(usp_m.group(1).replace(',', '.'))
            qty_m = re.search(r'(\d+[\.,]?\d*)\s*(?:ml|g|kg|l)\b', text, re.IGNORECASE)
            if qty_m and usp_val > 0:
                qty_val = float(qty_m.group(1).replace(',', '.'))
                calc_mrp = round(qty_val * usp_val)
                if 1.0 <= calc_mrp <= 50000:
                    return {"value": float(calc_mrp), "has_tax_note": has_tax_note, "raw": f"MRP Rs. {calc_mrp:.2f} (from USP Rs. {usp_val:g}/ml)"}
        except Exception:
            pass

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1).replace(',', '.'))
                if 0.5 <= value <= 100000:
                    return {"value": value, "has_tax_note": has_tax_note, "raw": f"MRP Rs. {value:.2f}"}
            except ValueError:
                continue

    # Fallback: scan lines containing MRP keywords
    for line in text.split('\n'):
        if re.search(r'\b(?:MRP|M\.R\.P|MEP|Max\.?\s*Retail\s*Price|Retail\s*Price)\b', line, re.IGNORECASE):
            m = re.search(r'(?:Rs\.?|₹|INR|[?{\[\(<\|~/\\*#;])*\s*(\d+[\.,]\d{1,2}|\d+)', line)
            if m:
                try:
                    val = float(m.group(1).replace(',', '.'))
                    if 0.5 <= val <= 100000:
                        return {"value": val, "has_tax_note": has_tax_note, "raw": f"MRP Rs. {val:.2f}"}
                except ValueError:
                    pass

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
            value = float(match.group(1).replace(',', '.'))
            if value <= 0:
                continue
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

    lines = text.split('\n')
    stop_pattern = r'\b(?:MRP|M\.R\.P|Net\s+Qty|Net\s+Quantity|Best\s+Before|Expiry|Exp\b|Date|Batch|Lot\b|Ingredients|Nutri|FSSAI|Lic|Issai|Consumer|Customer|Toll|Country|Product\s+Name)\b'

    # Fallback: scan lines for manufacturer keywords (but NOT "Mfg/Packaging" which is a date field)
    for i, line in enumerate(lines):
        if re.search(r'Mfg\s*/?\s*Packag|Date\s+of\s+Mfg', line, re.IGNORECASE):
            continue
        if re.search(r'(?:Manufactured|Packed|Packer|Marketed|Imported|Mfd|Pkg)', line, re.IGNORECASE):
            addr_lines = [line]
            for j in range(i + 1, min(i + 6, len(lines))):
                if re.search(stop_pattern, lines[j], re.IGNORECASE):
                    break
                addr_lines.append(lines[j])
            addr = ' '.join(addr_lines).strip()
            if len(addr) > 10:
                nearby_text = ' '.join(lines[max(0, i-1):min(i+7, len(lines))])
                has_pincode = bool(re.search(r'\b\d{6}\b', nearby_text))
                return {"value": addr, "has_pincode": has_pincode, "raw": addr}

    # Fallback 2: Look for lines with 6-digit pincode or address keywords (e.g. Plot No, Sector, Pvt Ltd)
    for i, line in enumerate(lines):
        if re.search(r'\b\d{6}\b', line) or re.search(r'\b(?:Plot\s+No|Sector|Pvt|Ltd|Limited)\b', line, re.IGNORECASE):
            start_idx = max(0, i - 1) if i > 0 and not re.search(stop_pattern, lines[i-1], re.IGNORECASE) else i
            addr_lines = []
            for j in range(start_idx, min(i + 4, len(lines))):
                if j != start_idx and re.search(stop_pattern, lines[j], re.IGNORECASE):
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
    # Flexible date regex: DD/MM/YYYY or DD/MM or MM/YYYY with optional spaces around delimiters
    date_val_pattern = r'(?:(?:0?[1-9]|[12]\d|3[01])\s*[\/\-\.]\s*(?:0?[1-9]|1[0-2])(?:\s*[\/\-\.]\s*(?:20\d{2}|19\d{2}|\d{2}))?|(?:0?[1-9]|1[0-2])\s*[\/\-\.]\s*(?:20\d{2}|19\d{2}|2[0-9])|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*(?:\d{1,2},?\s*)?(?:20\d{2}|19\d{2}|\d{2}))'

    delim = r'[:\.\-\s\[\(\{\|]*'
    mfg_patterns = [
        r'(?:(?:Date\s+of\s+)?(?:Mfg|Manufactur\w*|Packag\w*|Pack\w*|MFD|PKD)(?:\s*(?:[\/\&]|and|,|\s)\s*(?:Mfg|Manufactur\w*|Packag\w*|Pack\w*|MFD|PKD))*\s*(?:Date\s*(?:of)?)?|(?:Mfg|Packag\w*|Pack\w*)\s*(?:Date\s+of)?|Date\s+of\s+[\w\s\/]+)\s*' + delim + r'(' + date_val_pattern + r')',
        r'(?:Mfg|MFD|PKD|PKG)\s*' + delim + r'(' + date_val_pattern + r')',
    ]
    exp_patterns = [
        r'(?:Exp(?:iry)?\.?\s*(?:Date|Dt\.?)?|Best\s+Before|Use\s+Before|Use\s+By|BB)\s*(?:[A-Za-z\s]{0,15})?' + delim + r'(' + date_val_pattern + r'|\d+\s*(?:months?|days?|years?))',
    ]
    for pattern in mfg_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["manufacture_date"] = {"value": match.group(1).strip(), "raw": match.group(0).strip()}
            break
    for pattern in exp_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["expiry_date"] = {"value": match.group(1).strip(), "raw": match.group(0).strip()}
            break

    # Line-by-line fallback if mfg date still not found
    if "manufacture_date" not in result:
        lines = text.split('\n')
        for idx, line in enumerate(lines):
            if re.search(r'\b(?:Toll\s*Free|Helpline|Consumer\s*Care|Customer\s*Care|Phone|Tel\b|Fax\b|Call\s+Us)\b', line, re.IGNORECASE):
                continue
            if re.search(r'\b(?:Mfg|Packag\w*|Pack\w*|MFD|PKD|Manufactur\w*)\b', line, re.IGNORECASE):
                dm = re.search(date_val_pattern, line, re.IGNORECASE)
                if dm:
                    result["manufacture_date"] = {"value": dm.group(0).strip(), "raw": line.strip()}
                    break
                if idx + 1 < len(lines):
                    dm_next = re.search(r'^\s*' + delim + r'(' + date_val_pattern + r')\b', lines[idx + 1], re.IGNORECASE)
                    if dm_next:
                        result["manufacture_date"] = {"value": dm_next.group(1).strip(), "raw": f"{line.strip()} {lines[idx+1].strip()}"}
                        break

    # If still not found, search for standalone date near top of packaging or dates in text
    if not result:
        standalone_m = re.search(date_val_pattern, text, re.IGNORECASE)
        if standalone_m:
            result["manufacture_date"] = {"value": standalone_m.group(0).strip(), "raw": standalone_m.group(0).strip()}

    return result if result else None


def extract_consumer_care(text: str) -> Optional[dict]:
    result = {}
    phone = re.search(r'(?:Consumer\s*Care|Customer\s*Care|Helpline|Toll\s*Free|Contact|Call(?:\s+Us)?(?:\s+At)?)\s*[:\.\-]?\s*([\+]?[\d\s\-]{7,15})', text, re.IGNORECASE)
    if phone:
        result["phone"] = phone.group(1).strip()
    if not result.get("phone"):
        phone_any = re.search(r'(?:1800|1860)[\s\-]?(?:\d{2,4}[\s\-]?\d{3,4}|\d{6,7})', text)
        if phone_any:
            result["phone"] = phone_any.group(0).strip()
    email = re.search(r'[\w\.\-]+@[\w\.\-]+\.\w+', text)
    if email:
        result["email"] = email.group(0).strip()
    feedback_match = re.search(r'(?:Consumer\s*(?:Services\s*)?Manager|Feedback\s*(?:or\s*)?Queries|Write\s+to\s*:)', text, re.IGNORECASE)
    if feedback_match and not result.get("details"):
        result["details"] = "Consumer services contact present on package"
    return result if result else None


def extract_country_of_origin(text: str) -> Optional[str]:
    patterns = [
        r'(?:Country\s+of\s+Origin|Made\s+in|Product\s+of|Manufactured\s+in)\s*[:\.]?\s*([A-Za-z\s]+?)(?:\n|\.|\,|$)',
        r'(?:Origin)\s*[:\.]?\s*([A-Za-z\s]+?)(?:\n|\.|\,|$)',
    ]
    known_countries = [
        'India', 'USA', 'United States', 'China', 'UK', 'United Kingdom', 'Thailand',
        'Vietnam', 'Indonesia', 'Malaysia', 'Sri Lanka', 'Bangladesh', 'Nepal',
        'Germany', 'Italy', 'Japan', 'Korea', 'Australia', 'New Zealand', 'France', 'Spain', 'Singapore'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_country = match.group(1).strip()
            for c in known_countries:
                if re.search(r'\b' + re.escape(c) + r'\b', raw_country, re.IGNORECASE):
                    return c.upper() if c.upper() in ['USA', 'UK'] else c.title()
            cleaned = re.split(r'[;:,.\(\)\[\]\{\}\n]', raw_country)[0].strip()
            words = cleaned.split()
            if words:
                return ' '.join(words[:2]).strip()

    # Default to India if Indian packaging markers are present
    if re.search(r'\b(?:FSSAI|Rs\.?|₹|Legal\s+Metrology|coca-cola\s+india|New\s+Delhi|Mumbai|Gurugram|Odisha|Karnataka)\b', text, re.IGNORECASE):
        return "India"

    return None


def extract_common_name(text: str, master_product: Optional[dict] = None) -> Optional[str]:
    """Extract product name — prefer master product name or explicit 'Product Name' field."""
    if master_product and isinstance(master_product, dict) and master_product.get("name"):
        m_name = str(master_product.get("name"))
        keywords = [w.lower() for w in re.split(r'\W+', m_name) if len(w) > 3]
        if any(kw in text.lower() for kw in keywords):
            return m_name

    def clean_name(val: str) -> str:
        val = val.strip().rstrip('.,;- ')
        val = re.sub(r'\s*(?:Agent|Acidity|Anticaking|Emulsifier|Stabilizer|Flavour|Flavor|Preservative|Color|Colour|INS)\b.*$', '', val, flags=re.IGNORECASE)
        return val.strip().rstrip('.,;- ')

    # Explicit "Product Name" label
    product_name_match = re.search(
        r'(?:Product\s+Name|Name\s+of\s+(?:the\s+)?(?:Product|Commodity|Food))\s*[:\.]?\s*(.+?)(?:\n|$)',
        text, re.IGNORECASE
    )
    if product_name_match:
        name = clean_name(product_name_match.group(1))
        if len(name) > 2 and not re.search(r'PANEL|\[|\]|^[-—_=]{2,}', name):
            return name

    # Common FMCG product categories
    prod_pattern = r'\b(Potato\s+Chips|Chips|Biscuits|Cookies|Namkeen|Noodles|Snacks|Tea|Coffee|Chocolate|Atta|Wheat\s+Flour|Rice|Cooking\s+Oil|Edible\s+Oil|Spices?|Masala|Mango\s+Drink|Fruit\s+Drink|Juice|Soft\s+Drink|Beverage|Milk|Soda|Cola|Energy\s+Drink)\b'
    match_cat = re.search(prod_pattern, text, re.IGNORECASE)
    if match_cat:
        return match_cat.group(1).title()

    # Fallback: scan lines, ignoring panel markers and section titles
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or len(line) < 3:
            continue
        if re.search(r'PANEL|\[|\]|^[-—_=\*#\s]{2,}', line, re.IGNORECASE):
            continue
        if re.match(r'^(?:STORE|PAPER|PWM|MIMIMUM|papen|CniL|26|751|recycled)\b', line, re.IGNORECASE):
            continue
        if re.match(r'^(MRP|M\.R\.P|MEP|USP|Unit|Rs\.?|INR|Net|Date|Batch|FSSAI|Lic|Consumer|Country|Manufacturer|Ingredients|Nutri|Energy|Protein|Fat|Carb|Sugar|Sodium|Approx|Values|Per|Serving|IMUTR)', line, re.IGNORECASE):
            continue
        if re.search(r'\b(?:Pvt|Ltd|Limited|LLP|Inc|Corp|Beverages)\b', line, re.IGNORECASE):
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

    if master_product and isinstance(master_product, dict) and master_product.get("name"):
        return str(master_product.get("name"))

    return None


def extract_batch_number(text: str) -> Optional[str]:
    patterns = [
        r'\b(?:Batch\s+(?:No\.?|Number)|Lot\s+(?:No\.?|Number))\s*[:\.\-\s\[\(\{|]*([A-Za-z0-9][\w\-\/]+)',
        r'\b(?:B\.?\s*No\.?|L\.?\s*No\.?)\s*[:\.\-\s\[\(\{|]*([A-Za-z0-9][\w\-\/]+)',
        r'\b(?:Batch|Lot)\s*[:\.\-\s\[\(\{|]+(?!Number\b|No\b)([A-Za-z0-9][\w\-\/]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if len(val) >= 3 and not re.match(r'^(?:Number|No|Date|Code|and|of|for)$', val, re.IGNORECASE):
                return val
    return None


def extract_fssai(text: str) -> Optional[str]:
    match = re.search(r'(?:FSSAI|Lic(?:ense)?[\s\.;:\-]*No[\.;:\-]*)[\s\.;:\-,\(\[\{]*(\d{14})', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    fssai_structured = re.search(r'(?<!\d)([12]\d{13})(?!\d)', text)
    if fssai_structured:
        return fssai_structured.group(1).strip()
    fssai_only = re.search(r'(?<!\d)(\d{14})(?!\d)', text)
    if fssai_only:
        return fssai_only.group(1).strip()
    return None


def extract_all_fields(text: str, master_product: Optional[dict] = None) -> dict:
    fields = {}
    mrp = extract_mrp(text)
    if mrp:
        fields["mrp"] = mrp

    net_qty = extract_net_quantity(text)
    if net_qty:
        fields["net_quantity"] = net_qty

    manufacturer = extract_manufacturer(text)
    if manufacturer:
        if not manufacturer.get("has_pincode") and re.search(r'\b\d{6}\b', text):
            manufacturer["has_pincode"] = True
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

    common_name = extract_common_name(text, master_product)
    if common_name:
        fields["common_name"] = common_name

    batch = extract_batch_number(text)
    if batch:
        fields["batch_number"] = batch

    fssai = extract_fssai(text)
    if fssai:
        fields["fssai_license"] = fssai

    fields["_raw_text"] = text
    return fields
