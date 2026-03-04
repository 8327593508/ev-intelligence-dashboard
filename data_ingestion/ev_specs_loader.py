# ===============================================================
# File: data_ingestion/ev_specs_loader.py
# Purpose: Load Custom EV Specs into Production DB (NORMALIZED)
# FIXED: Uses canonical manufacturer resolution + FK integrity
# ===============================================================

import csv
from sqlalchemy import text
from database.db_connection import get_engine

# 🔥 CRITICAL: Use the SAME normalizer across ALL loaders
from data_ingestion.manufacturer_normalizer import normalize_manufacturer


def load_ev_specs(csv_path):

    print("🚀 Loading EV Specs (Normalized Mode)...")

    engine = get_engine()

    with engine.begin() as conn:

        # ---------------------------------------------
        # 1️⃣ Load vehicle type map once (performance)
        # ---------------------------------------------
        result = conn.execute(text("""
            SELECT vehicle_type_id, type_name
            FROM vehicle_types
        """)).fetchall()

        vehicle_type_map = {
            row[1].upper(): row[0] for row in result
        }

        with open(csv_path, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:

                # ---------------------------------------------
                # 2️⃣ Normalize manufacturer (CRITICAL STEP)
                # ---------------------------------------------
                raw_manufacturer = str(row["manufacturer"]).strip()
                manufacturer_name = normalize_manufacturer(raw_manufacturer)

                if not manufacturer_name:
                    continue

                # ---------------------------------------------
                # 3️⃣ UPSERT manufacturer (no duplicates)
                # ---------------------------------------------
                conn.execute(text("""
                    INSERT INTO manufacturers (manufacturer_name)
                    VALUES (:name)
                    ON CONFLICT (manufacturer_name) DO NOTHING
                """), {"name": manufacturer_name})

                # Fetch correct manufacturer_id (normalized)
                manufacturer_id = conn.execute(text("""
                    SELECT manufacturer_id
                    FROM manufacturers
                    WHERE manufacturer_name = :name
                """), {"name": manufacturer_name}).scalar()

                if not manufacturer_id:
                    continue

                # ---------------------------------------------
                # 4️⃣ Resolve vehicle type (FK safe)
                # ---------------------------------------------
                vehicle_type = str(row["vehicle_type"]).strip().upper()

                if vehicle_type not in vehicle_type_map:
                    print(f"⚠ Vehicle type not found: {vehicle_type}")
                    continue

                vehicle_type_id = vehicle_type_map[vehicle_type]

                # ---------------------------------------------
                # 5️⃣ Insert EV specs (dedup safe)
                # ---------------------------------------------
                conn.execute(text("""
                    INSERT INTO ev_vehicle_specs
                    (model_name, manufacturer_id, vehicle_type_id,
                     price, range_km, battery_capacity_kwh, charging_time_hr)
                    VALUES
                    (:model, :manufacturer_id, :vehicle_type_id,
                     :price, :range_km, :battery, :charging)
                    ON CONFLICT (model_name) DO UPDATE SET
                        price = EXCLUDED.price,
                        range_km = EXCLUDED.range_km,
                        battery_capacity_kwh = EXCLUDED.battery_capacity_kwh,
                        charging_time_hr = EXCLUDED.charging_time_hr
                """), {
                    "model": row["model_name"].strip(),
                    "manufacturer_id": manufacturer_id,
                    "vehicle_type_id": vehicle_type_id,
                    "price": float(row["price"]) if row["price"] else None,
                    "range_km": float(row["range_km"]) if row["range_km"] else None,
                    "battery": float(row["battery_capacity_kwh"]) if row["battery_capacity_kwh"] else None,
                    "charging": float(row["charging_time_hr"]) if row["charging_time_hr"] else None
                })

    print("✅ EV Specs Loaded Successfully (Normalized & FK-Safe)!")


if __name__ == "__main__":
    load_ev_specs("data_sources/ev_vehicles_specs_india.csv")
