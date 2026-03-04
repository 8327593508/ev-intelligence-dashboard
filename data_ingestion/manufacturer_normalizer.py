# ==========================================================
# File: data_ingestion/manufacturer_normalizer.py
# Purpose: Normalize manufacturer names across ALL datasets
# Safe for: Location + Sales + Specs CSV
# ==========================================================

import re


# Legal suffix words ONLY (safe to remove)
LEGAL_SUFFIXES = [
    "PVT LTD",
    "PRIVATE LIMITED",
    "LTD",
    "LIMITED",
    "LLP",
    "INC",
    "CORP",
    "CORPORATION",
]


# Canonical brand mapping (IMPORTANT for cross-dataset matching)
CANONICAL_MAPPING = {
    # Major EV brands (India)
    "TATA MOTORS": "Tata Motors",
    "TATA": "Tata Motors",

    "MAHINDRA ELECTRIC": "Mahindra",
    "MAHINDRA": "Mahindra",

    "MG MOTOR INDIA": "MG Motor",
    "MG": "MG Motor",

    "OLA ELECTRIC": "Ola Electric",
    "ATHER ENERGY": "Ather",
    "HERO ELECTRIC": "Hero Electric",

    "TVS MOTOR COMPANY": "TVS Motor",
    "TVS MOTOR": "TVS Motor",

    "VOLVO GROUP INDIA": "Volvo",
    "VOLVO": "Volvo",
}


def normalize_manufacturer(name: str) -> str:
    """
    Standardize manufacturer names WITHOUT destroying brand identity.
    
    Fixes:
    - Case mismatches
    - Legal suffix variations (PVT LTD, LTD, etc.)
    - Cross-dataset naming inconsistencies
    """

    if not name:
        return None

    # Step 1: Basic cleaning
    name = str(name).strip().upper()
    name = name.replace('"', '')  # remove quotes if present

    # Step 2: Remove ONLY legal suffixes (safe)
    for suffix in LEGAL_SUFFIXES:
        name = name.replace(suffix, "")

    # Step 3: Remove extra spaces & special chars
    name = re.sub(r"[^\w\s&]", " ", name)  # keep & for names like A & CO
    name = re.sub(r"\s+", " ", name).strip()

    # Step 4: Apply canonical mapping (CRITICAL)
    if name in CANONICAL_MAPPING:
        return CANONICAL_MAPPING[name]

    # Step 5: Return cleaned Title Case (default)
    return name.title()
