# ==========================================================
# File: data_ingestion/manufacturer_location_loader.py
# Purpose: Load & Standardize Manufacturer HQ Location
# FIXED: Handles normalization + UPSERT + NULL-safe HQ updates
# ==========================================================

import pandas as pd
from sqlalchemy import text
from database.db_connection import get_engine

# 🔥 IMPORTANT: Use the correct normalizer (NOT mapper)
from data_ingestion.manufacturer_normalizer import normalize_manufacturer


def load_manufacturer_locations(csv_path):
    print("🏭 Loading Manufacturer Location Data (Clean + Normalized Mode)...")

    # Load CSV
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    engine = get_engine()

    inserted = 0
    updated = 0

    with engine.begin() as conn:
        for _, row in df.iterrows():

            # -------------------------------
            # Step 1: Extract raw fields
            # -------------------------------
            raw_name = str(row["EV Maker"]).strip()
            city = str(row["Place"]).strip() if pd.notna(row["Place"]) else None
            state = str(row["State"]).strip() if pd.notna(row["State"]) else None

            # -------------------------------
            # Step 2: Normalize manufacturer name
            # (CRITICAL for cross-CSV matching)
            # -------------------------------
            manufacturer_name = normalize_manufacturer(raw_name)

            if not manufacturer_name:
                continue

            # -------------------------------
            # Step 3: UPSERT Manufacturer (Production Safe)
            # - Prevent duplicates
            # - Fill HQ only if NULL
            # - Preserve existing good HQ data
            # -------------------------------
            result = conn.execute(text("""
                INSERT INTO manufacturers (
                    manufacturer_name,
                    headquarters_city,
                    headquarters_state
                )
                VALUES (
                    :name,
                    :city,
                    :state
                )
                ON CONFLICT (manufacturer_name)
                DO UPDATE SET
                    headquarters_city = COALESCE(
                        manufacturers.headquarters_city,
                        EXCLUDED.headquarters_city
                    ),
                    headquarters_state = COALESCE(
                        manufacturers.headquarters_state,
                        EXCLUDED.headquarters_state
                    )
                RETURNING xmax = 0 AS inserted_flag;
            """), {
                "name": manufacturer_name,
                "city": city,
                "state": state
            })

            # PostgreSQL trick: xmax=0 → inserted, else updated
            flag = result.fetchone()[0]
            if flag:
                inserted += 1
            else:
                updated += 1

    print(f"🆕 Manufacturers Inserted: {inserted}")
    print(f"🔄 Manufacturers Updated (HQ filled if NULL): {updated}")
    print("🎯 Manufacturer Location Data Loaded Successfully (Normalized + Deduplicated)!")


if __name__ == "__main__":
    load_manufacturer_locations("data_sources/EV Maker by Place.csv")
