FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

RUN pip install -r ai_agent/requirements.txt
RUN pip install -r requirements.txt

ENV PYTHONPATH=/app

CMD ["python", "pipeline_runner.py"]
