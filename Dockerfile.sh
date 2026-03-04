FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --upgrade pip
RUN pip install -r ai_agent/requirements.txt

CMD ["python", "pipeline_runner.py"]