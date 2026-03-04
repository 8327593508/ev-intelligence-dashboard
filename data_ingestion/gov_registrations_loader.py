# ==========================================================
# File: data_ingestion/gov_registrations_loader.py
# Purpose: Load Government EV Registration Data (Optimized + Stable)
# Fixes:
# - Pagination support
# - Neon-safe batch insert
# - Data cleaning
# - Robust API handling
# ==========================================================

import requests
import os
from database.db_connection import get_engine
from sqlalchemy import text
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_KEY = os.getenv("DATA_GOV_API_KEY")
BASE_URL = "https://api.data.gov.in/resource"
RESOURCE_ID = "492b2b53-64b7-4cd7-bc8b-2096abb55f3c"


def load_gov_registrations():
    print("🚀 Fetching Government EV Registration Data (ALL Pages)...")

    if not API_KEY:
        print("❌ ERROR: DATA_GOV_API_KEY not found in .env file")
        return

    engine = get_engine()
    offset = 0
    limit = 1000
    total_inserted = 0

    while True:
        params = {
            "api-key": API_KEY,
            "format": "json",
            "limit": limit,
            "offset": offset
        }

        response = requests.get(f"{BASE_URL}/{RESOURCE_ID}", params=params)

        if response.status_code != 200:
            print("❌ API Error:", response.text)
            break

        records = response.json().get("records", [])

        if not records:
            print("✅ No more records found. Pagination complete.")
            break

        print(f"📦 Processing batch: {len(records)} records (offset={offset})")

        batch_data = []

        for record in records:
            state = record.get("state_name")

            if not state:
                continue

            try:
                year = int(record.get("year", datetime.now().year))
            except:
                year = datetime.now().year

            vehicle_data = {
                "2W": record.get("two_wheeler"),
                "3W": record.get("three_wheeler"),
                "4W": record.get("four_wheeler"),
            }

            for v_type, count in vehicle_data.items():
                if not count or count == "NA":
                    continue

                try:
                    count = int(count)
                except:
                    continue

                if count <= 0:
                    continue

                batch_data.append({
                    "state": state.strip(),
                    "vehicle_type": v_type,
                    "count": count,
                    "year": year,
                    "month": 1,
                    "source": "DataGov"
                })

        if not batch_data:
            offset += limit
            continue

        # 🔥 Neon-safe batch insert
        with engine.begin() as conn:
            for row in batch_data:
                result = conn.execute(
                    text("""
                        SELECT vehicle_type_id 
                        FROM vehicle_types 
                        WHERE type_name = :type
                    """),
                    {"type": row["vehicle_type"]}
                ).fetchone()

                if not result:
                    continue

                vehicle_type_id = result[0]

                conn.execute(text("""
                    INSERT INTO ev_registrations
                    (state, vehicle_type_id, registration_count, year, month, source)
                    VALUES (:state, :vehicle_type_id, :count, :year, :month, :source)
                    ON CONFLICT (state, vehicle_type_id, year, month)
                    DO UPDATE SET registration_count = EXCLUDED.registration_count
                """), {
                    "state": row["state"],
                    "vehicle_type_id": vehicle_type_id,
                    "count": row["count"],
                    "year": row["year"],
                    "month": row["month"],
                    "source": row["source"]
                })

        total_inserted += len(batch_data)
        print(f"✅ Inserted so far: {total_inserted}")

        offset += limit

    print(f"🎯 Government EV Registration Data Loaded! Total: {total_inserted}")


if __name__ == "__main__":
    print("🔄 Running Real-Time Govt API Pipeline via Agent...")
    load_gov_registrations()
    print("✅ DataGov Pipeline Completed Successfully!")

