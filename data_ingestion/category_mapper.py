# ===============================================================
# File: data_ingestion/category_mapper.py
# Purpose: Standardize EV categories across all datasets
# ===============================================================

CATEGORY_MAPPING = {

    # ===== Two Wheeler Variants =====
    "2W": "TWO_WHEELER",
    "TWO WHEELER(NT)": "TWO_WHEELER",
    "TWO WHEELER(T)": "TWO_WHEELER",
    "TWO WHEELER (INVALID CARRIAGE)": "TWO_WHEELER",

    # ===== Three Wheeler Variants =====
    "3W": "THREE_WHEELER",
    "THREE WHEELER(NT)": "THREE_WHEELER",
    "THREE WHEELER(T)": "THREE_WHEELER",

    # ===== Four Wheeler Variants =====
    "4W": "FOUR_WHEELER",
    "FOUR WHEELER (INVALID CARRIAGE)": "FOUR_WHEELER",

    # ===== LMV Variants =====
    "LMV": "LIGHT_MOTOR_VEHICLE",
    "LIGHT MOTOR VEHICLE": "LIGHT_MOTOR_VEHICLE",

    # ===== Goods Vehicles =====
    "LIGHT GOODS VEHICLE": "LIGHT_GOODS_VEHICLE",
    "MEDIUM GOODS VEHICLE": "MEDIUM_GOODS_VEHICLE",
    "HEAVY GOODS VEHICLE": "HEAVY_GOODS_VEHICLE",

    # ===== Passenger Vehicles =====
    "LIGHT PASSENGER VEHICLE": "LIGHT_PASSENGER_VEHICLE",
    "MEDIUM PASSENGER VEHICLE": "MEDIUM_PASSENGER_VEHICLE",
    "HEAVY PASSENGER VEHICLE": "HEAVY_PASSENGER_VEHICLE",

    # ===== Other =====
    "OTHER THAN MENTIONED ABOVE": "OTHER"
}


def normalize_category(raw_category: str) -> str:
    """
    Convert raw dataset category into standardized category.
    If category not found, return 'OTHER'
    """
    raw_category = raw_category.strip().upper()
    return CATEGORY_MAPPING.get(raw_category, "OTHER")
