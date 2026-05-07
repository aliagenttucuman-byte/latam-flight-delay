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
COPY static/ ./static/

# Generate context.json during build (only once)
RUN python -c "from challenge.ai_insights import generate_and_save_context; generate_and_save_context()"

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

ENV PORT=8080

CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8080"]