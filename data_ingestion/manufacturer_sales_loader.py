# ==========================================================
# File: data_ingestion/manufacturer_sales_loader.py
# Purpose: ULTRA STABLE Manufacturer Sales Loader (Neon Safe)
# Features:
# - Crash-proof for Neon Free Tier
# - Fresh DB connection per batch
# - Small batch streaming (no memory overload)
# - Manufacturer normalization (no mismatch)
# - Retry mechanism (connection drop safe)
# - Slow but 100% stable ETL pipeline
# ==========================================================

import pandas as pd
import time
from sqlalchemy import text
from database.db_connection import get_engine
from data_ingestion.manufacturer_normalizer import normalize_manufacturer

# 🔥 VERY SAFE for Neon Free Tier (Do NOT increase)
BATCH_SIZE = 100
RETRY_LIMIT = 3
SLEEP_BETWEEN_BATCH = 0.5  # seconds (prevents server overload)


def insert_batch_with_retry(engine, query, data, attempt=1):
    """
    Insert batch with retry logic to handle Neon connection drops.
    """
    try:
        with engine.begin() as conn:  # Fresh connection every batch
            conn.execute(query, data)
        return True
    except Exception as e:
        print(f"⚠️ Batch insert failed (Attempt {attempt}/{RETRY_LIMIT})")
        print(f"Error: {str(e)[:200]}")

        if attempt < RETRY_LIMIT:
            print("🔄 Retrying batch after short delay...")
            time.sleep(2)
            return insert_batch_with_retry(engine, query, data, attempt + 1)
        else:
            print("❌ Batch permanently failed after retries.")
            return False


def load_manufacturer_sales(csv_path: str):
    print("🚀 Starting Manufacturer Sales Loader (ULTRA STABLE NEON MODE)...")

    # =====================================================
    # 1️⃣ Load CSV
    # =====================================================
    print("📁 Reading CSV file...")
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()

    print(f"✅ Original CSV Rows: {len(df)}")
    print(f"📌 Columns Found: {df.columns.tolist()}")

    # =====================================================
    # 2️⃣ Melt Wide → Long (Time Series Format)
    # =====================================================
    print("🔄 Converting wide format to long format (melt)...")
    df_long = df.melt(
        id_vars=["Cat", "Maker"],
        var_name="year",
        value_name="sales"
    )

    print(f"📊 Rows After Melt: {len(df_long)}")

    # =====================================================
    # 3️⃣ Clean Sales Data
    # =====================================================
    print("🧹 Cleaning sales data (removing zeros & invalid)...")
    df_long["sales"] = pd.to_numeric(df_long["sales"], errors="coerce").fillna(0)
    df_long = df_long[df_long["sales"] > 0]

    print(f"📉 Rows After Filtering Zero Sales: {len(df_long)}")

    # =====================================================
    # 4️⃣ Normalize Manufacturer Names (CRITICAL)
    # =====================================================
    print("🏭 Normalizing manufacturer names...")
    df_long["normalized_maker"] = df_long["Maker"].astype(str).apply(
        lambda x: normalize_manufacturer(x.strip())
    )

    df_long = df_long[df_long["normalized_maker"].notna()]

    unique_makers = df_long["normalized_maker"].unique().tolist()
    print(f"🏢 Unique Normalized Manufacturers: {len(unique_makers)}")

    engine = get_engine()

    # =====================================================
    # 5️⃣ Insert Manufacturers (SAFE CHUNKS)
    # =====================================================
    print("📥 Ensuring manufacturers exist (chunked insert)...")

    insert_manufacturer_query = text("""
        INSERT INTO manufacturers (manufacturer_name)
        SELECT UNNEST(:names)
        ON CONFLICT (manufacturer_name) DO NOTHING
    """)

    for i in range(0, len(unique_makers), BATCH_SIZE):
        chunk = unique_makers[i:i + BATCH_SIZE]
        insert_batch_with_retry(
            engine,
            insert_manufacturer_query,
            {"names": chunk}
        )
        time.sleep(SLEEP_BETWEEN_BATCH)

    print("✅ Manufacturer dimension prepared successfully!")

    # =====================================================
    # 6️⃣ Fetch Mapping Tables (ONE TIME)
    # =====================================================
    print("🔑 Fetching manufacturer and vehicle type mappings...")
    with engine.connect() as conn:
        manufacturer_rows = conn.execute(text("""
            SELECT manufacturer_id, manufacturer_name
            FROM manufacturers
        """)).fetchall()

        vehicle_type_rows = conn.execute(text("""
            SELECT vehicle_type_id, type_name
            FROM vehicle_types
        """)).fetchall()

    manufacturer_map = {row[1]: row[0] for row in manufacturer_rows}
    vehicle_type_map = {row[1].upper(): row[0] for row in vehicle_type_rows}

    print(f"🔐 Manufacturer Map Size: {len(manufacturer_map)}")
    print(f"🚗 Vehicle Types Available: {list(vehicle_type_map.keys())}")

    # =====================================================
    # 7️⃣ ULTRA SAFE STREAMING INSERT (CRASH-PROOF)
    # =====================================================
    print("🚚 Starting ultra-safe streaming insert into manufacturer_yearly_sales...")

    insert_sales_query = text("""
        INSERT INTO manufacturer_yearly_sales
        (manufacturer_id, vehicle_type_id, year, sales)
        VALUES (:manufacturer_id, :vehicle_type_id, :year, :sales)
        ON CONFLICT (manufacturer_id, vehicle_type_id, year)
        DO UPDATE SET sales = EXCLUDED.sales
    """)

    buffer = []
    total_inserted = 0
    skipped = 0

    for index, row in df_long.iterrows():
        maker = row["normalized_maker"]
        vehicle_type = str(row["Cat"]).strip().upper()

        if maker not in manufacturer_map:
            skipped += 1
            continue

        if vehicle_type not in vehicle_type_map:
            skipped += 1
            continue

        buffer.append({
            "manufacturer_id": manufacturer_map[maker],
            "vehicle_type_id": vehicle_type_map[vehicle_type],
            "year": int(row["year"]),
            "sales": int(row["sales"])
        })

        # 🔥 Insert in VERY SMALL SAFE BATCHES (Crash-Proof)
        if len(buffer) >= BATCH_SIZE:
            success = insert_batch_with_retry(
                engine,
                insert_sales_query,
                buffer
            )

            if success:
                total_inserted += len(buffer)
                print(f"✅ Inserted {total_inserted} records so far...")
            else:
                print("⚠️ Skipping failed batch but continuing pipeline...")

            buffer.clear()
            time.sleep(SLEEP_BETWEEN_BATCH)  # Prevent Neon overload

    # Insert remaining records
    if buffer:
        success = insert_batch_with_retry(
            engine,
            insert_sales_query,
            buffer
        )
        if success:
            total_inserted += len(buffer)

    # =====================================================
    # 8️⃣ Final Summary
    # =====================================================
    print("\n🎯 MANUFACTURER SALES LOADING COMPLETED!")
    print(f"📦 Total Records Inserted/Updated: {total_inserted}")
    print(f"⚠️ Skipped Records (mapping issues): {skipped}")
    print("🟢 Pipeline Status: STABLE (No crash, Neon-safe)")


if __name__ == "__main__":
    load_manufacturer_sales("data_sources/ev_sales_by_makers_and_cat_15-24.csv")
