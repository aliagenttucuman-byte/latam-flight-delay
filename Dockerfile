# syntax=docker/dockerfile:1.2
# Changes from original: Dockerfile was empty skeleton with only "# put you docker configuration here"
# See: Plan_Ejecucion.md section "Cambios Realizados vs Original"
FROM python:3.11-slim

WORKDIR /app

COPY requirements*.txt ./

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-test.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

COPY challenge/ ./challenge/
COPY data/ ./data/

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8000"]