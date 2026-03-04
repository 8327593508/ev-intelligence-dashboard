# ===============================================================
# File: ml_pipeline/predict_lstm.py
# Purpose: Production Inference Pipeline (Full Plot + Forecast CSV)
# Features:
# - Loads trained LSTM model safely
# - Handles scaler mismatch
# - Plots Actual + Fitted + Future Forecast
# - Saves forecast CSV for dashboard
# - Crash-proof sequence generation
# ===============================================================

import os
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model

# ==============================
# CONFIG (MATCH TRAINING)
# ==============================
DATA_PATH = "data_sources/ev_india_monthly.csv"
MODEL_PATH = "ml_pipeline/artifacts/lstm_ev_model.h5"
SCALER_PATH = "ml_pipeline/artifacts/scaler.save"
OUTPUT_FORECAST_PATH = "artifacts/future_forecast_inference.csv"
PLOT_PATH = "artifacts/prediction_plot.png"

LOOKBACK = 12        # MUST match training
FUTURE_STEPS = 12    # 12 months forecast


# ===============================================================
# LOAD & PREPROCESS DATA (SAFE + CONSISTENT WITH TRAINING)
# ===============================================================
def load_data():
    print("📂 Loading dataset for inference...")

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"❌ CSV not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # Clean column names
    df.columns = [col.strip() for col in df.columns]

    # Validate required columns
    if "date" not in df.columns or "total_ev_registrations" not in df.columns:
        raise ValueError("CSV must contain 'date' and 'total_ev_registrations' columns")

    # Convert and sort date
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Remove messy or zero rows (prevents sharp drops)
    df = df[df["total_ev_registrations"] > 0]

    # Set index for plotting
    df.set_index("date", inplace=True)

    print(f"📊 Records Loaded: {len(df)}")
    print(f"📅 Date Range: {df.index.min()} → {df.index.max()}")

    return df


# ===============================================================
# CREATE LSTM SEQUENCES (CRASH-PROOF)
# ===============================================================
def create_sequences(data, lookback):
    X = []
    for i in range(lookback, len(data)):
        X.append(data[i - lookback:i])
    return np.array(X)


# ===============================================================
# MAIN INFERENCE PIPELINE
# ===============================================================
def main():
    print("🔮 Starting Production LSTM Inference Pipeline...")

    # ==============================
    # LOAD DATA
    # ==============================
    df = load_data()
    values = df[["total_ev_registrations"]].values  # ensure single feature

    # ==============================
    # LOAD SCALER (STRICT 1-FEATURE COMPATIBILITY)
    # ==============================
    if not os.path.exists(SCALER_PATH):
        raise FileNotFoundError("❌ Scaler not found. Run training first.")

    scaler = joblib.load(SCALER_PATH)

    # Ensure correct shape for scaler (fixes 'X has 8 features' error)
    scaled_data = scaler.transform(values)

    # ==============================
    # LOAD MODEL (SAFE DESERIALIZATION)
    # ==============================
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("❌ Model file not found. Train the model first.")

    # compile=False avoids keras.metrics.mse error
    model = load_model(MODEL_PATH, compile=False)

    print("✅ Model & Scaler loaded successfully")

    # ==============================
    # PREPARE LAST SEQUENCE
    # ==============================
    if len(scaled_data) < LOOKBACK:
        raise ValueError(f"❌ Not enough data. Need at least {LOOKBACK} rows.")

    last_sequence = scaled_data[-LOOKBACK:]
    last_sequence = last_sequence.reshape(1, LOOKBACK, 1)

    # ==============================
    # FUTURE FORECAST (12 MONTHS)
    # ==============================
    print("📈 Forecasting next 12 months (recursive)...")

    future_predictions = []
    current_sequence = last_sequence.copy()

    for _ in range(FUTURE_STEPS):
        pred_scaled = model.predict(current_sequence, verbose=0)

        # Safe scalar extraction
        pred_value = float(pred_scaled[0][0])
        future_predictions.append(pred_value)

        # Update sequence (NO dimension crash)
        new_step = np.array([[[pred_value]]])  # shape (1,1,1)
        current_sequence = np.concatenate(
            (current_sequence[:, 1:, :], new_step), axis=1
        )

    # Inverse scale predictions
    future_predictions = np.array(future_predictions).reshape(-1, 1)
    future_predictions = scaler.inverse_transform(future_predictions).flatten()

    # Create future dates
    last_date = df.index[-1]
    future_dates = pd.date_range(
        start=last_date + pd.DateOffset(months=1),
        periods=FUTURE_STEPS,
        freq="MS"
    )

    forecast_df = pd.DataFrame({
        "date": future_dates,
        "predicted_ev_registrations": future_predictions
    })

    # Save forecast CSV (for dashboard/API)
    os.makedirs("artifacts", exist_ok=True)
    forecast_df.to_csv(OUTPUT_FORECAST_PATH, index=False)
    print(f"💾 Future forecast saved at: {OUTPUT_FORECAST_PATH}")

    # ===============================================================
    # GENERATE FULL PRODUCTION PLOT (ACTUAL + FITTED + FUTURE)
    # ===============================================================
    print("📊 Generating full production plot...")

    # Historical fitted predictions (smooth orange line)
    X_hist = create_sequences(scaled_data, LOOKBACK)
    X_hist = X_hist.reshape((X_hist.shape[0], X_hist.shape[1], 1))

    hist_pred_scaled = model.predict(X_hist, verbose=0)
    hist_pred = scaler.inverse_transform(hist_pred_scaled).flatten()

    # Align dates due to lookback window
    hist_dates = df.index[LOOKBACK:]

    plt.figure(figsize=(14, 6))

    # Actual data
    plt.plot(
        df.index,
        df["total_ev_registrations"],
        label="Actual EV Registrations",
        linewidth=2
    )

    # Smooth fitted curve (THIS is the missing orange line)
    plt.plot(
        hist_dates,
        hist_pred,
        label="LSTM Fitted Prediction",
        color="orange",
        linewidth=2
    )

    # Future forecast (dashed)
    plt.plot(
        forecast_df["date"],
        forecast_df["predicted_ev_registrations"],
        linestyle="--",
        color="red",
        linewidth=2,
        label="Future Forecast (12 Months)"
    )

    plt.title("EV Registration Forecast (Inference - Production)")
    plt.xlabel("Date")
    plt.ylabel("EV Registrations")
    plt.legend()
    plt.grid(True)

    plt.savefig(PLOT_PATH, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"🖼️ Full prediction plot saved at: {PLOT_PATH}")
    print("🚀 Production inference pipeline completed successfully!")


# ===============================================================
# ENTRY POINT
# ===============================================================
if __name__ == "__main__":
    main()
