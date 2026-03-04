# ===============================================================
# File: ml_pipeline/train_lstm.py
# FINAL STABLE VERSION (Scaler + Model Sync)
# Multivariate Ready | Crash-Proof | Metrics + Forecast Saving
# ===============================================================

import os
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.metrics import mean_squared_error, mean_absolute_error

from ml_pipeline.feature_engineering import load_and_preprocess

# CONFIG
DATA_PATH = "data_sources/ev_india_monthly.csv"
ARTIFACT_DIR = "ml_pipeline/artifacts"
MODEL_PATH = f"{ARTIFACT_DIR}/lstm_ev_model.h5"
SCALER_PATH = f"{ARTIFACT_DIR}/scaler.save"
FORECAST_PATH = "artifacts/future_forecast.csv"
METRICS_PATH = "artifacts/metrics.txt"

LOOKBACK = 12
FUTURE_STEPS = 12
EPOCHS = 25
BATCH_SIZE = 8


def create_model(input_shape):
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(32),
        Dropout(0.2),
        Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse")
    return model


def main():
    print("🚀 Starting LSTM Training Pipeline (FINAL CLEAN)...")

    # Create artifact folders
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    os.makedirs("artifacts", exist_ok=True)

    # Load processed data (SINGLE SOURCE OF TRUTH)
    X, y, scaler, df = load_and_preprocess(DATA_PATH, sequence_length=LOOKBACK)

    print(f"📊 Training Samples: {X.shape}")
    print(f"📅 Data Range: {df['date'].min()} → {df['date'].max()}")

    # Train/Test Split (Time-Series Safe)
    split_index = int(len(X) * 0.8)
    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    # Build Model
    model = create_model((X.shape[1], X.shape[2]))

    # Train
    print("🧠 Training LSTM model...")
    history = model.fit(
        X_train, y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_data=(X_test, y_test),
        verbose=1
    )

    # Save Model (WITHOUT optimizer state to avoid Keras errors)
    model.save(MODEL_PATH, include_optimizer=False)

    # 🚨 CRITICAL: Save the SAME scaler used for training
    joblib.dump(scaler, SCALER_PATH)
    print("💾 Model & Scaler saved successfully")

    # Predictions (Inverse Scaling)
    y_pred_scaled = model.predict(X_test)
    y_pred = scaler.inverse_transform(y_pred_scaled.reshape(-1, 1))
    y_test_actual = scaler.inverse_transform(y_test.reshape(-1, 1))

    # Metrics
    rmse = np.sqrt(mean_squared_error(y_test_actual, y_pred))
    mae = mean_absolute_error(y_test_actual, y_pred)
    mape = np.mean(np.abs((y_test_actual - y_pred) / y_test_actual)) * 100

    with open(METRICS_PATH, "w") as f:
        f.write(f"RMSE: {rmse:.2f}\n")
        f.write(f"MAE: {mae:.2f}\n")
        f.write(f"MAPE: {mape:.2f}%\n")

    print("\n📊 MODEL METRICS:")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAE: {mae:.2f}")
    print(f"MAPE: {mape:.2f}%")

    # ================= FUTURE FORECAST =================
    print("📈 Forecasting next 12 months...")

    last_sequence = X[-1].reshape(1, LOOKBACK, 1)
    future_preds = []

    for _ in range(FUTURE_STEPS):
        pred_scaled = model.predict(last_sequence, verbose=0)
        pred_value = float(pred_scaled[0][0])
        future_preds.append(pred_value)

        new_step = np.array([[[pred_value]]])
        last_sequence = np.concatenate(
            (last_sequence[:, 1:, :], new_step),
            axis=1
        )

    # Inverse scale forecast
    future_preds = scaler.inverse_transform(
        np.array(future_preds).reshape(-1, 1)
    ).flatten()

    # Create dates
    last_date = pd.to_datetime(df["date"]).max()
    future_dates = pd.date_range(
        start=last_date + pd.DateOffset(months=1),
        periods=FUTURE_STEPS,
        freq="MS"
    )

    forecast_df = pd.DataFrame({
        "date": future_dates,
        "forecast_ev_registrations": future_preds
    })

    forecast_df.to_csv(FORECAST_PATH, index=False)
    print(f"💾 Future forecast saved at: {FORECAST_PATH}")


if __name__ == "__main__":
    main()
