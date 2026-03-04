import subprocess

print("Starting EV data ingestion...")

subprocess.run(["python", "data_ingestion/gov_registrations_loader.py"], check=True)

print("Running feature engineering...")
subprocess.run(["python", "ml_pipeline/feature_engineering.py"], check=True)

print("Training LSTM model...")
subprocess.run(["python", "ml_pipeline/train_lstm.py"], check=True)

print("Generating predictions...")
subprocess.run(["python", "ml_pipeline/predict_lstm.py"], check=True)

print("Saving forecast to database...")
subprocess.run(["python", "ml_pipeline/save_forecast_to_db.py"], check=True)

print("Pipeline completed successfully.")