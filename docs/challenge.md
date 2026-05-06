# Flight Delay Prediction API - Technical Documentation

## Project Overview

Operationalize a flight delay prediction model for SCL airport using XGBoost, deployed as FastAPI with CI/CD on GCP.

**Original Challenge:** Machine Learning & LLMs LAN LATAM
**Status:** Complete

---

## Model Architecture

### XGBoost with Top 10 Features

The model uses XGBoost (chosen over Logistic Regression for better handling of categorical features) with the top 10 features identified in the exploration phase:

| Feature | Description |
|---------|-------------|
| `OPERA_Latin American Wings` | Airline dummy (highest correlation with delay) |
| `MES_7` | July - winter month |
| `MES_10` | October |
| `OPERA_Grupo LATAM` | LATAM group airline |
| `MES_12` | December |
| `TIPOVUELO_I` | International flight |
| `MES_4` | April |
| `MES_11` | November |
| `OPERA_Sky Airline` | Low-cost airline |
| `OPERA_Copa Air` | Copa Airlines |

### Class Balancing

The dataset is imbalanced (~85% no delay, ~15% delay). Class balancing is applied via `scale_pos_weight = n_y0/n_y1`, improving recall for class 1 from ~0.3 to >0.6.

---

## API Design

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/predict` | POST | Predict delays for batch of flights |

### Request Format

```json
{
  "flights": [
    {
      "OPERA": "LATAM",
      "TIPOVUELO": "I",
      "MES": 6
    }
  ]
}
```

### Response Format

```json
{
  "predict": [1]
}
```

### Validated Values

- **OPERA**: 16 airlines from the dataset
- **TIPOVUELO**: `I` (International), `N` (National)
- **MES**: 1-12

---

## Changes from Original Challenge

Per README.md instructions ("create extra classes and methods" and "apply all good programming practices"), the following changes were made:

| File | Change | Justification |
|------|--------|---------------|
| `requirements.txt` | Updated to FastAPI 0.115+, Pydantic 2.x, uvicorn 0.30+ | httpx 1.0+ broke testclient compatibility with old starlette; upgrade ecosystem |
| `challenge/api.py` | Used `@field_validator` instead of `@validator` | Pydantic 2.x syntax (original used Pydantic 1.10.2 `@validator`) |
| `Dockerfile` | Completed (was empty skeleton), uses PORT=8080 | Cloud Run requirement; original skeleton wouldn't deploy |
| `docker-compose.yml` | Created | Development workflow with hot-reload |
| `model.py` | Removed `use_label_encoder=True` | Deprecated parameter in XGBoost 1.5+ |

All changes are documented with inline comments referencing `Plan_Ejecucion.md` section "Cambios Realizados vs Original" for full audit trail.

---

## Deployment

### Deployed API

**Production URL:** `https://delay-model-api-chxpmithta-rj.a.run.app`

**Test endpoint:**
```bash
curl -X POST "https://delay-model-api-chxpmithta-rj.a.run.app/predict" \
  -H "Content-Type: application/json" \
  -d '{"flights":[{"OPERA":"Grupo LATAM","TIPOVUELO":"I","MES":7}]}'
```

### Local Development

```bash
# Build and run
docker build -t delay-model-api:local .
docker run -p 8000:8000 delay-model-api:local

# Or use docker-compose (hot-reload)
docker-compose up --build
```

### GCP Cloud Run

```bash
gcloud run deploy delay-model-api \
  --source . \
  --region southamerica-east1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512M \
  --cpu 1
```

### CI/CD

- **CI Workflow** (`.github/workflows/ci.yml`): Runs model and API tests on push/PR
- **CD Workflow** (`.github/workflows/cd.yml`): Deploys to Cloud Run on merge to main

**Important:** Cloud Run expects containers to listen on `PORT=8080` (injected automatically). Ensure Dockerfile exposes port 8080 and uvicorn runs on that port.

---

## Testing

### Unit Tests

```bash
# API tests
python -m pytest tests/api/test_api.py -v

# Model tests (from tests/model directory)
cd tests/model && python -m pytest test_model.py -v && cd ../..
```

### Stress Tests

```bash
# 50 users, 30 seconds
python -m locust -f tests/stress/api_stress.py --print-stats --headless --users 50 --spawn-rate 5 -H http://localhost:8000 --run-time 30s
```

**Results**: 2,180 requests, 0 failures, ~75 RPS, P95: 940ms

---

## Architecture Diagram

```
Client Request → FastAPI Validation → load_model() (lazy singleton) → Prediction Pipeline → Response
                    (Pydantic)           (trains on first call)         (XGBoost predict)
```

---

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| XGBoost over Logistic Regression | Better handling of categorical features via get_dummies |
| Top 10 features | Speed optimization while maintaining recall > 0.60 |
| Lazy model loading | Memory efficient - trains only when first prediction requested |
| Class balancing | Without it, recall for delay class is ~0.3, with it >0.6 |

---

## References

- Full development documentation: `Plan_Ejecucion.md`
- Stress test results: Above in this document
- Model code: `challenge/model.py`
- API code: `challenge/api.py`

---

## CD Deployment Errors Log (2026-05-06)

During first GitHub Actions deployment to GCP Cloud Run, the following errors occurred and were resolved:

### Error 1: YAML Syntax Error

GitHub Actions `run:` blocks interpret `$()` as template syntax, not shell. `$(gcloud ...)` in `run:` caused YAML parse error.

**Fix:** Remove problematic steps or escape with `$$`.

### Error 2: SA Lacked Permission for `gcloud services enable`

`gcloud.services.enable` requires specific roles the SA didn't have.

**Fix:** APIs were already enabled. Remove `gcloud services enable` from workflow.

### Error 3: Artifact Registry Repo Missing

`gcloud run deploy --source .` requires `cloud-run-source-deploy` repo in Artifact Registry.

**Fix:** Create repo manually:
```bash
gcloud artifacts repositories create cloud-run-source-deploy \
  --repository-format=docker --location=southamerica-east1
```

### Error 4: Cloud Build SA Needed Artifact Registry Permissions

`--source .` uses Cloud Build internally. Cloud Build SA (`32555940559@cloudbuild.gserviceaccount.com`) needs `artifactregistry.writer` on the repo.

**Fix:**
```bash
gcloud artifacts repositories add-iam-policy-binding cloud-run-source-deploy \
  --location=southamerica-east1 \
  --member="serviceAccount:32555940559@cloudbuild.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"
gcloud projects add-iam-policy-binding latam-flight-delay \
  --member="serviceAccount:32555940559@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Error 5: GitHub Actions SA Needed `cloudbuild.builds.builder`

**Fix:**
```bash
gcloud projects add-iam-policy-binding latam-flight-delay \
  --member="serviceAccount:github-actions@latam-flight-delay.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"
```

### Error 6: Dockerfile PORT Mismatch

Cloud Run injects `PORT=8080`. Original Dockerfile used port 8000, causing container startup failure.

**Fix:** Update Dockerfile:
```dockerfile
EXPOSE 8080
ENV PORT=8080
CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

### IAM Roles Summary

| Service Account | Resource | Role |
|-----------------|----------|------|
| `github-actions@...` | Project | `artifactregistry.admin`, `artifactregistry.writer`, `cloudbuild.builds.builder`, `run.admin` |
| `github-actions@...` | Repo `cloud-run-source-deploy` | `artifactregistry.admin`, `artifactregistry.writer` |
| `32555940559@cloudbuild.gserviceaccount.com` | Repo `cloud-run-source-deploy` | `artifactregistry.writer` |
| `32555940559@cloudbuild.gserviceaccount.com` | Project | `run.admin` |