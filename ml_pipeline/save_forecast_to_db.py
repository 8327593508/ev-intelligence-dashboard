import pandas as pd
from sqlalchemy import text
from database.db_connection import get_engine

FORECAST_CSV = "artifacts/future_forecast_inference.csv"

def save_forecast():
    print("📦 Saving forecast to Neon PostgreSQL...")

    df = pd.read_csv(FORECAST_CSV)

    engine = get_engine()

    with engine.begin() as conn:
        # Create table if not exists
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ev_forecast (
            date DATE PRIMARY KEY,
            predicted_ev_registrations NUMERIC
        );
        """))

        # Insert forecast rows
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO ev_forecast (date, predicted_ev_registrations)
                VALUES (:date, :value)
                ON CONFLICT (date) DO UPDATE
                SET predicted_ev_registrations = EXCLUDED.predicted_ev_registrations;
            """), {
                "date": row["date"],
                "value": float(row["predicted_ev_registrations"])
            })

    print("✅ Forecast stored in database successfully!")

if __name__ == "__main__":
    save_forecast()
