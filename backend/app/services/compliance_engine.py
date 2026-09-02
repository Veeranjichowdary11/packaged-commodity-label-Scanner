from typing import Optional


RULES = [
    {
        "code": "LM-R6-NAME",
        "name": "Name of Commodity",
        "section": "Rule 6(1)(a)",
        "field": "common_name",
        "required": True,
        "severity": "critical",
        "description": "The package shall bear the name or description indicating the true nature of the commodity.",
    },
    {
        "code": "LM-R6-NETQTY",
        "name": "Net Quantity Declaration",
        "section": "Rule 6(1)(b)",
        "field": "net_quantity",
        "required": True,
        "severity": "critical",
        "description": "Net quantity by weight, measure or number shall be declared on the package.",
    },
    {
        "code": "LM-R6-NETQTY-UNIT",
        "name": "Net Quantity - Standard Units",
        "section": "Rule 6(2)",
        "field": "net_quantity",
        "required": False,
        "severity": "major",
        "description": "Net quantity shall be expressed in standard units of weight or measure as per the Act.",
        "check": "unit_standard",
    },
    {
        "code": "LM-R6-MFG",
        "name": "Manufacturer/Packer Name & Address",
        "section": "Rule 6(1)(c)",
        "field": "manufacturer",
        "required": True,
        "severity": "critical",
        "description": "Name and complete address of the manufacturer or packer or importer shall be declared.",
    },
    {
        "code": "LM-R6-MFG-PIN",
        "name": "Manufacturer Address - Pin Code",
        "section": "Rule 6(1)(c)",
        "field": "manufacturer",
        "required": False,
        "severity": "major",
        "description": "The address of the manufacturer/packer shall include the pin code.",
        "check": "pincode",
    },
    {
        "code": "LM-R6-MRP",
        "name": "Maximum Retail Price",
        "section": "Rule 6(1)(e)",
        "field": "mrp",
        "required": True,
        "severity": "critical",
        "description": "The retail sale price (MRP) of the package shall be declared.",
    },
    {
        "code": "LM-R6-MRP-TAX",
        "name": "MRP - Inclusive of All Taxes",
        "section": "Rule 6(1)(e)",
        "field": "mrp",
        "required": False,
        "severity": "major",
        "description": "MRP shall be inclusive of all taxes and shall state 'inclusive of all taxes'.",
        "check": "tax_inclusive",
    },
    {
        "code": "LM-R6-DATE",
        "name": "Month and Year of Manufacture/Packing",
        "section": "Rule 6(1)(d)",
        "field": "dates",
        "required": True,
        "severity": "critical",
        "description": "Month and year in which the commodity is manufactured, packed or imported shall be declared.",
    },
    {
        "code": "LM-R6-CARE",
        "name": "Consumer Care Details",
        "section": "Rule 6(1)(g)",
        "field": "consumer_care",
        "required": True,
        "severity": "major",
        "description": "Consumer care details including contact number and email shall be declared.",
    },
    {
        "code": "LM-R6-COUNTRY",
        "name": "Country of Origin",
        "section": "Rule 6(1)(h)",
        "field": "country_of_origin",
        "required": True,
        "severity": "major",
        "description": "Country of origin shall be declared for imported packages.",
    },
]

STANDARD_UNITS = {"g", "kg", "ml", "L", "cm", "mm", "m", "pcs", "nos", "units"}

MIN_FONT_SIZE_MM = {
    100: 1,
    500: 2,
    2500: 4,
    float("inf"): 6,
}


def check_compliance(extracted_fields: dict, is_imported: bool = False) -> dict:
    violations = []
    passed = []
    checks_run = 0

    for rule in RULES:
        if rule["code"] == "LM-R6-COUNTRY" and not is_imported:
            continue

        checks_run += 1
        field_name = rule["field"]
        field_value = extracted_fields.get(field_name)

        if rule["required"] and field_value is None:
            violations.append({
                "rule_code": rule["code"],
                "rule_name": rule["name"],
                "description": f"MISSING: {rule['description']}",
                "severity": rule["severity"],
                "field_name": field_name,
                "expected_value": "Present on label",
                "actual_value": "Not found",
                "section_reference": rule["section"],
            })
            continue

        if field_value is None:
            continue

        check_type = rule.get("check")

        if check_type == "tax_inclusive" and isinstance(field_value, dict):
            if not field_value.get("has_tax_note", False):
                violations.append({
                    "rule_code": rule["code"],
                    "rule_name": rule["name"],
                    "description": f"NON-COMPLIANT: {rule['description']}",
                    "severity": rule["severity"],
                    "field_name": field_name,
                    "expected_value": "MRP inclusive of all taxes",
                    "actual_value": field_value.get("raw", ""),
                    "section_reference": rule["section"],
                })
            else:
                passed.append(rule["code"])
            continue

        if check_type == "pincode" and isinstance(field_value, dict):
            if not field_value.get("has_pincode", False):
                violations.append({
                    "rule_code": rule["code"],
                    "rule_name": rule["name"],
                    "description": f"NON-COMPLIANT: {rule['description']}",
                    "severity": rule["severity"],
                    "field_name": field_name,
                    "expected_value": "Address with 6-digit pin code",
                    "actual_value": field_value.get("value", ""),
                    "section_reference": rule["section"],
                })
            else:
                passed.append(rule["code"])
            continue

        if check_type == "unit_standard" and isinstance(field_value, dict):
            unit = field_value.get("unit", "")
            if unit not in STANDARD_UNITS:
                violations.append({
                    "rule_code": rule["code"],
                    "rule_name": rule["name"],
                    "description": f"NON-COMPLIANT: {rule['description']}",
                    "severity": rule["severity"],
                    "field_name": field_name,
                    "expected_value": f"Standard unit ({', '.join(STANDARD_UNITS)})",
                    "actual_value": unit,
                    "section_reference": rule["section"],
                })
            else:
                passed.append(rule["code"])
            continue

        passed.append(rule["code"])

    total = checks_run
    failed = len(violations)
    passed_count = total - failed

    if failed == 0:
        status = "compliant"
    elif passed_count / total >= 0.7:
        status = "partially_compliant"
    else:
        status = "non_compliant"

    score = round((passed_count / total) * 100, 1) if total > 0 else 0

    return {
        "status": status,
        "score": score,
        "total_checks": total,
        "passed_checks": passed_count,
        "failed_checks": failed,
        "violations": violations,
        "passed_rules": passed,
    }
