import subprocess

print("Starting EV data ingestion...")

subprocess.run(["python", "-m", "data_ingestion.gov_registrations_loader"], check=True)

print("Running feature engineering...")
subprocess.run(["python", "-m", "ml_pipeline.feature_engineering"], check=True)

print("Training LSTM model...")
subprocess.run(["python", "-m", "ml_pipeline.train_lstm"], check=True)

print("Generating predictions...")
subprocess.run(["python", "-m", "ml_pipeline.predict_lstm"], check=True)

print("Saving forecast to database...")
subprocess.run(["python", "-m", "ml_pipeline.save_forecast_to_db"], check=True)

print("Pipeline completed successfully.")
