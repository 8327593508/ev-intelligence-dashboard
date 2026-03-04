# ===============================================================
# EV Intelligence Production Schema (FINAL STABLE VERSION)
# ML + DL Ready | Neon PostgreSQL | SQLAlchemy 2.x
# ===============================================================

from database.db_connection import get_engine
from sqlalchemy import text


def create_tables():
    engine = get_engine()

    with engine.begin() as conn:

        # ===================================================
        # 1️⃣ VEHICLE TYPES
        # ===================================================
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS vehicle_types (
            vehicle_type_id SERIAL PRIMARY KEY,
            type_name TEXT UNIQUE NOT NULL
        );
        """))

        conn.execute(text("""
        INSERT INTO vehicle_types (type_name) VALUES
        ('2W'),
        ('3W'),
        ('4W'),
        ('BUS'),
        ('LMV'),
        ('MMV')
        ON CONFLICT (type_name) DO NOTHING;
        """))

        # ===================================================
        # 2️⃣ MANUFACTURERS (WITH LOCATION)
        # ===================================================
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS manufacturers (
            manufacturer_id SERIAL PRIMARY KEY,
            manufacturer_name TEXT UNIQUE NOT NULL,

            headquarters_city TEXT,
            headquarters_state TEXT,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))

        # ===================================================
        # 3️⃣ EV VEHICLE SPECS
        # ===================================================
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ev_vehicle_specs (
            vehicle_id SERIAL PRIMARY KEY,
            model_name TEXT UNIQUE NOT NULL,
            manufacturer_id INT NOT NULL,
            vehicle_type_id INT NOT NULL,

            price DOUBLE PRECISION,
            range_km DOUBLE PRECISION,
            battery_capacity_kwh DOUBLE PRECISION,
            charging_time_hr DOUBLE PRECISION,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (manufacturer_id)
                REFERENCES manufacturers(manufacturer_id)
                ON DELETE RESTRICT,

            FOREIGN KEY (vehicle_type_id)
                REFERENCES vehicle_types(vehicle_type_id)
                ON DELETE RESTRICT
        );
        """))

        # ===================================================
        # 4️⃣ EV REGISTRATIONS (TIME SERIES)
        # ===================================================
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ev_registrations (
            registration_id SERIAL PRIMARY KEY,

            state TEXT NOT NULL DEFAULT 'India',
            vehicle_type_id INT NOT NULL,

            registration_count INT NOT NULL CHECK (registration_count >= 0),

            year INT NOT NULL CHECK (year >= 2000),
            month INT NOT NULL DEFAULT 1 CHECK (month BETWEEN 1 AND 12),

            source TEXT DEFAULT 'UNKNOWN',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (vehicle_type_id)
                REFERENCES vehicle_types(vehicle_type_id)
                ON DELETE RESTRICT,

            UNIQUE(state, vehicle_type_id, year, month)
        );
        """))

        # ===================================================
        # 5️⃣ MANUFACTURER YEARLY SALES
        # ===================================================
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS manufacturer_yearly_sales (
            id SERIAL PRIMARY KEY,

            manufacturer_id INT NOT NULL,
            vehicle_type_id INT NOT NULL,

            year INT NOT NULL CHECK (year >= 2000),
            sales INT NOT NULL CHECK (sales >= 0),

            FOREIGN KEY (manufacturer_id)
                REFERENCES manufacturers(manufacturer_id)
                ON DELETE RESTRICT,

            FOREIGN KEY (vehicle_type_id)
                REFERENCES vehicle_types(vehicle_type_id)
                ON DELETE RESTRICT,

            UNIQUE(manufacturer_id, vehicle_type_id, year)
        );
        """))

        # ===================================================
        # 6️⃣ CHARGING STATIONS
        # ===================================================
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS charging_stations (
            station_id TEXT PRIMARY KEY,

            operator TEXT,
            city TEXT,
            state TEXT,
            country TEXT DEFAULT 'India',

            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,

            power_kw DOUBLE PRECISION,
            connection_type TEXT,
            charger_level TEXT,
            num_connectors INT DEFAULT 0,

            source TEXT DEFAULT 'OpenChargeMap',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP
        );
        """))

    print("✅ EV Production Database Created Successfully!")


if __name__ == "__main__":
    create_tables()
