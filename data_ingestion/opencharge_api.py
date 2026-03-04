# ============================================================
# File: data_ingestion/opencharge_api.py
# Purpose: India EV Charging Stations Data Ingestion Pipeline
# Source: OpenChargeMap API
# Database: Neon PostgreSQL (SQLAlchemy 2.x compatible)
# ============================================================

import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import text
from database.db_connection import get_engine


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES (.env file)
# ============================================================
# This loads your OPENCHARGE_API_KEY from .env
load_dotenv()

# Get API key securely from environment
API_KEY = os.getenv("OPENCHARGE_API_KEY")


# ============================================================
# 2. FETCH INDIA-ONLY EV CHARGING DATA (STABLE - NO PAGINATION)
# ============================================================
def fetch_india_charging_data():
    """
    Fetch EV charging station data for India only.
    
    Why no pagination?
    - OpenChargeMap does NOT support true page-based pagination
    - Using loops can cause infinite fetch issues
    - maxresults=1000 is sufficient for India dataset
    """

    url = (
        "https://api.openchargemap.io/v3/poi/"
        f"?output=json"
        f"&countrycode=IN"      # Filter: India only 🇮🇳
        f"&maxresults=1000"     # Fetch up to 1000 Indian stations
        f"&key={API_KEY}"
    )

    print("🚀 Starting India EV Data Fetch...")
    print(f"🔑 API Key Loaded: {'Yes' if API_KEY else 'No'}")

    # Send API request
    response = requests.get(url, timeout=60)

    # Raise error if API fails (important for debugging)
    response.raise_for_status()

    # Convert response to JSON list
    data = response.json()

    print(f"📦 Total records fetched from API: {len(data)}")

    return data


# ============================================================
# 3. SAFE EXTRACTION FROM NESTED API JSON (CRITICAL FIX)
# ============================================================
def extract_station_fields(station):
    """
    Safely extract fields from OpenChargeMap nested JSON.
    
    IMPORTANT:
    - Many API records have NULL or missing fields
    - We must use .get() and fallback {} to avoid crashes
    """

    # AddressInfo may be None → use fallback {}
    address = station.get("AddressInfo") or {}

    # Operator info may be missing
    operator_info = station.get("OperatorInfo") or {}

    # Connections list may be empty or None
    connections = station.get("Connections") or []

    # ---------------- Core Required Fields ----------------
    station_id = str(station.get("ID"))

    latitude = address.get("Latitude")
    longitude = address.get("Longitude")

    # Location fields (useful for India analysis)
    city = address.get("Town")
    state = address.get("StateOrProvince")
    country = "India"  # Fixed since we filter countrycode=IN

    # Operator name (may be NULL in real dataset)
    operator = operator_info.get("Title")

    # ---------------- Optional Charger Fields ----------------
    power_kw = None
    connection_type = None
    charger_level = None
    num_connectors = 0

    # Extract connection details safely
    if isinstance(connections, list) and len(connections) > 0:
        num_connectors = len(connections)

        first_conn = connections[0] or {}

        # Power rating (kW)
        power_kw = first_conn.get("PowerKW")

        # Charger connection type (CCS, Type2, etc.)
        if first_conn.get("ConnectionType"):
            connection_type = first_conn["ConnectionType"].get("Title")

        # Charger level (Fast, Slow, Rapid)
        if first_conn.get("Level"):
            charger_level = first_conn["Level"].get("Title")

    # Return dictionary for SQL insertion
    return {
        "station_id": station_id,
        "operator": operator,
        "latitude": latitude,
        "longitude": longitude,
        "city": city,
        "state": state,
        "country": country,
        "power_kw": power_kw,
        "connection_type": connection_type,
        "charger_level": charger_level,
        "num_connectors": num_connectors,
        "source": "OpenChargeMap",
        "last_updated": datetime.utcnow(),
    }


# ============================================================
# 4. STORE DATA INTO NEON POSTGRESQL (UPSERT - DAILY SAFE)
# ============================================================
def store_charging_data(data):
    """
    Store EV charging data into PostgreSQL (Neon).
    
    Features:
    - UPSERT to avoid duplicate records
    - Null-safe insertion
    - Skips only invalid coordinate records
    - Auto commit using engine.begin()
    """

    engine = get_engine()
    inserted = 0
    skipped = 0

    # engine.begin() ensures auto-commit (VERY IMPORTANT for Neon)
    with engine.begin() as conn:
        for station in data:
            try:
                # Extract cleaned fields
                record = extract_station_fields(station)

                # Skip only if coordinates are missing (invalid geo data)
                if record["latitude"] is None or record["longitude"] is None:
                    skipped += 1
                    continue

                # SQLAlchemy 2.x compatible parameterized query
                conn.execute(
                    text("""
                    INSERT INTO charging_stations (
                        station_id,
                        operator,
                        latitude,
                        longitude,
                        city,
                        state,
                        country,
                        power_kw,
                        connection_type,
                        charger_level,
                        num_connectors,
                        source,
                        last_updated
                    )
                    VALUES (
                        :station_id,
                        :operator,
                        :latitude,
                        :longitude,
                        :city,
                        :state,
                        :country,
                        :power_kw,
                        :connection_type,
                        :charger_level,
                        :num_connectors,
                        :source,
                        :last_updated
                    )
                    ON CONFLICT (station_id) DO UPDATE SET
                        operator = EXCLUDED.operator,
                        power_kw = EXCLUDED.power_kw,
                        connection_type = EXCLUDED.connection_type,
                        charger_level = EXCLUDED.charger_level,
                        num_connectors = EXCLUDED.num_connectors,
                        last_updated = EXCLUDED.last_updated;
                    """),
                    record,
                )

                inserted += 1

            except Exception as e:
                # Log bad records but do NOT crash pipeline
                skipped += 1
                print(f"⚠️ Error processing station {station.get('ID')}: {e}")

    print(f"✅ Records Inserted/Updated: {inserted}")
    print(f"⚠️ Records Skipped (Invalid/Missing Data): {skipped}")

    return inserted


# ============================================================
# 5. MAIN PIPELINE FUNCTION (END-TO-END ETL)
# ============================================================
def run_opencharge_india_pipeline():
    """
    Complete ETL Pipeline:
    Step 1: Fetch India EV Data (API)
    Step 2: Transform & Clean Data
    Step 3: Load into Neon PostgreSQL
    """

    print("🚀 Starting India EV Data Ingestion Pipeline...")

    # Step 1: Fetch data from API
    data = fetch_india_charging_data()

    # Safety check (very important)
    if not data:
        print("❌ No data fetched from API. Check API key or internet.")
        return

    print("🔄 Storing data into Neon PostgreSQL...")

    # Step 2 & 3: Store data into database
    inserted_count = store_charging_data(data)

    print("🎯 Pipeline Execution Completed Successfully!")
    print(f"📊 Total Records Processed: {len(data)}")
    print(f"💾 Total Records Inserted/Updated: {inserted_count}")


# ============================================================
# 6. SCRIPT ENTRY POINT
# ============================================================
# This ensures the pipeline runs only when file is executed directly
if __name__ == "__main__":
    run_opencharge_india_pipeline()
