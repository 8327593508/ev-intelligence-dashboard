# ==========================================================
# File: data_ingestion/kaggle_registration_loader.py
# Purpose: Load VAHAN Class-wise EV Registrations (Production Safe)
# Compatible with: ev_cat_01-24.csv (Your Actual File)
# ==========================================================

import pandas as pd
from database.db_connection import get_engine
from sqlalchemy import text
from datetime import datetime


def load_kaggle_registrations(csv_path):
    print("🚀 Loading VAHAN EV Registration Data (Deep Mode)...")

    # Load CSV
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    print("📊 Total Raw Rows:", len(df))
    print("📋 Columns Found:", df.columns.tolist())

    # ❗ Drop invalid first row (Date = 0)
    df = df[df["Date"] != 0]
    df = df.dropna(subset=["Date"])

    print("🧹 Rows after cleaning:", len(df))

    engine = get_engine()
    inserted = 0
    skipped = 0

    # Column groups mapping → Your DB schema
    two_wheeler_cols = [
        "TWO WHEELER(NT)",
        "TWO WHEELER(T)",
        "TWO WHEELER (INVALID CARRIAGE)"
    ]

    three_wheeler_cols = [
        "THREE WHEELER(NT)",
        "THREE WHEELER(T)"
    ]

    four_wheeler_cols = [
        "LIGHT MOTOR VEHICLE",
        "HEAVY MOTOR VEHICLE",
        "MEDIUM MOTOR VEHICLE",
        "LIGHT PASSENGER VEHICLE",
        "HEAVY PASSENGER VEHICLE",
        "LIGHT GOODS VEHICLE",
        "MEDIUM GOODS VEHICLE",
        "HEAVY GOODS VEHICLE",
        "FOUR WHEELER (INVALID CARRIAGE)"
    ]

    with engine.begin() as conn:

        # Fetch vehicle type IDs once (performance optimized)
        vehicle_type_map = {
            row[1]: row[0]
            for row in conn.execute(
                text("SELECT vehicle_type_id, type_name FROM vehicle_types")
            ).fetchall()
        }

        for _, row in df.iterrows():

            # 📅 Parse Date (DD/MM/YY format)
            try:
                date_obj = datetime.strptime(str(row["Date"]), "%d/%m/%y")
                year = date_obj.year
                month = date_obj.month
            except Exception:
                skipped += 1
                continue

            # 🛵 Aggregate 2W
            two_wheeler_count = sum(
                int(row.get(col, 0)) for col in two_wheeler_cols if col in df.columns
            )

            # 🛺 Aggregate 3W
            three_wheeler_count = sum(
                int(row.get(col, 0)) for col in three_wheeler_cols if col in df.columns
            )

            # 🚗 Aggregate 4W
            four_wheeler_count = sum(
                int(row.get(col, 0)) for col in four_wheeler_cols if col in df.columns
            )

            data_to_insert = [
                ("2W", two_wheeler_count),
                ("3W", three_wheeler_count),
                ("4W", four_wheeler_count),
            ]

            for v_type, count in data_to_insert:

                if count <= 0:
                    continue

                vehicle_type_id = vehicle_type_map.get(v_type)
                if not vehicle_type_id:
                    continue

                conn.execute(text("""
                    INSERT INTO ev_registrations
                    (state, vehicle_type_id, registration_count, year, month, source)
                    VALUES (:state, :vehicle_type_id, :count, :year, :month, :source)
                    ON CONFLICT (state, vehicle_type_id, year, month)
                    DO UPDATE SET registration_count = EXCLUDED.registration_count
                """), {
                    "state": "India",
                    "vehicle_type_id": vehicle_type_id,
                    "count": int(count),
                    "year": year,
                    "month": month,
                    "source": "VAHAN"
                })

                inserted += 1

            if inserted % 500 == 0 and inserted > 0:
                print(f"📥 Inserted {inserted} records so far...")

    print("\n🎯 VAHAN Registration Loading Completed!")
    print(f"✅ Total Inserted Records: {inserted}")
    print(f"⚠️ Skipped Rows (date issues): {skipped}")
    print("🧠 Dataset is now ML-ready (Monthly Time Series)")


if __name__ == "__main__":
    load_kaggle_registrations("data_sources/ev_cat_01-24.csv")
