# ===============================================================
# File: ml_pipeline/feature_engineering.py
# Purpose: Feature Engineering for EV Time Series (LSTM Ready)
# ===============================================================

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler


def load_and_preprocess(csv_path, sequence_length=12):
    """
    Load EV monthly data and convert into LSTM sequences.

    Args:
        csv_path (str): Path to ev_india_monthly.csv
        sequence_length (int): Number of past months to use (default = 12)

    Returns:
        X (numpy): Input sequences
        y (numpy): Target values
        scaler: Fitted scaler (for inverse transform)
        df: Original dataframe
    """

    print("📂 Loading EV monthly dataset...")

    # 1️⃣ Load CSV
    df = pd.read_csv(csv_path)

    # 2️⃣ Convert date column to datetime
    df["date"] = pd.to_datetime(df["date"])

    # 3️⃣ Sort by date (CRITICAL for time series)
    df = df.sort_values("date").reset_index(drop=True)

    print(f"📊 Total Records Found: {len(df)}")
    print(f"📅 Date Range: {df['date'].min()} → {df['date'].max()}")

    # 4️⃣ Extract target column
    values = df["total_ev_registrations"].values.reshape(-1, 1)

    # 5️⃣ Scale data (0 to 1) – Required for LSTM stability
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_values = scaler.fit_transform(values)

    # 6️⃣ Create sequences (Sliding Window)
    X = []
    y = []

    for i in range(sequence_length, len(scaled_values)):
        X.append(scaled_values[i-sequence_length:i, 0])
        y.append(scaled_values[i, 0])

    # Convert to numpy arrays
    X = np.array(X)
    y = np.array(y)

    # 7️⃣ Reshape for LSTM [samples, time_steps, features]
    X = np.reshape(X, (X.shape[0], X.shape[1], 1))

    print(f"🧠 LSTM Input Shape: {X.shape}")
    print(f"🎯 Target Shape: {y.shape}")

    return X, y, scaler, df
