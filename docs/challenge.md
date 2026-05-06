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
| `requirements.txt` | Updated numpy, pandas (Python 3.11 compatibility), added xgboost | Original versions don't compile on Python 3.11 |
| `Dockerfile` | Completed (was empty skeleton) | Required to make challenge executable |
| `docker-compose.yml` | Created | Development workflow with hot-reload |
| `challenge/api.py` | Used `@validator` instead of `@field_validator` | Pydantic 1.10.2 compatibility |

All changes are documented with inline comments referencing `Plan_Ejecucion.md` section "Cambios Realizados vs Original" for full audit trail.

---

## Deployment

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
  --allow-unauthenticated
```

### CI/CD

- **CI Workflow** (`.github/workflows/ci.yml`): Runs model and API tests on push/PR
- **CD Workflow** (`.github/workflows/cd.yml`): Deploys to Cloud Run on merge to main

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