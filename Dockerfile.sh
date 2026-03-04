FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy entire project
COPY . /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Install python dependencies
RUN pip install -r ai_agent/requirements.txt

# Run pipeline
CMD ["python", "pipeline_runner.py"]
