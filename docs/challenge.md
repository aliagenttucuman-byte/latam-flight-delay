# Flight Delay Prediction API - Technical Documentation

**Challenge:** Software Engineer (ML & LLMs) — LAN LATAM  
**Repository:** https://github.com/aliagenttucuman-byte/latam-flight-delay  
**Production URL:** https://delay-model-api-chxpmithta-rj.a.run.app  
**Status:** Complete and Deployed ✓

---

## 1. Challenge Compliance Summary

This section maps each requirement from the original `README.md` challenge to its implementation.

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Public GitHub repository | ✅ | [latam-flight-delay](https://github.com/aliagenttucuman-byte/latam-flight-delay) |
| Use `main` for releases | ✅ | CD auto-merges `develop` → `main` after successful deploy |
| GitFlow (no delete dev branches) | ✅ | `develop` branch preserved and actively used |
| Do not change challenge structure | ✅ | Original `challenge/`, `tests/`, `docs/` folders intact |
| Do not rename provided methods | ✅ | `DelayModel.preprocess()`, `fit()`, `predict()` signatures unchanged |
| Complete provided methods | ✅ | All methods implemented with full logic |
| Use FastAPI framework | ✅ | `challenge/api.py` uses FastAPI exclusively |
| Pass `make model-test` | ✅ | Model tests passing in CI |
| Pass `make api-test` | ✅ | API tests passing in CI |
| Deploy to cloud (GCP) | ✅ | Deployed on Cloud Run `southamerica-east1` |
| API URL in Makefile (line 26) | ✅ | `STRESS_URL = https://delay-model-api-chxpmithta-rj.a.run.app` |
| API remains deployed for review | ✅ | Active since 2026-05-06 |
| CI/CD with `.github/workflows/` | ✅ | `ci.yml` and `cd.yml` in `.github/workflows/` |
| Documentation in `docs/challenge.md` | ✅ | This document |

### Changes Made vs Original Skeleton

Per the challenge instructions ("*You can create the extra classes and methods you deem necessary*" and "*Apply all the good programming practices that you consider necessary*"), the following modifications were made:

| File | Change | Justification |
|------|--------|---------------|
| `requirements.txt` | Upgraded to FastAPI 0.115+, Pydantic 2.x, uvicorn 0.30+ | `httpx` 1.0+ broke `starlette` testclient compatibility; ecosystem upgrade required |
| `challenge/api.py` | Uses `@field_validator` (Pydantic v2 syntax) | Original skeleton used Pydantic 1.10.2 `@validator` |
| `Dockerfile` | Completed with `PORT=8080` | Cloud Run requires containers to listen on `PORT=8080`; original skeleton was empty |
| `docker-compose.yml` | Created for local dev | Hot-reload development workflow |
| `challenge/model.py` | Removed `use_label_encoder=True` | Parameter deprecated in XGBoost 1.5+ |
| `.github/workflows/ci.yml` | Added `ai-test` job | Tests for the additional `/ai-insights` endpoint |
| `.github/workflows/cd.yml` | Trigger on `develop`, auto-merge to `main` | GitFlow-compliant: develop for integration, main for releases |

---

## 2. Part I — Model (`challenge/model.py`)

### Model Selection: XGBoost

The Data Scientist evaluated multiple models in `exploration.ipynb`. **XGBoost** was selected over Logistic Regression because:

- Better handling of categorical features via `get_dummies`
- Greater robustness to overfitting with regularization
- Similar accuracy but superior recall on the minority class (delay=1)

### Top 10 Features

The model reduces ~50+ dummy features to the top 10, improving inference speed without degrading recall below the 0.60 threshold.

| Feature | Description |
|---------|-------------|
| `OPERA_Latin American Wings` | Airline dummy (highest delay correlation) |
| `MES_7` | July — winter peak |
| `MES_10` | October |
| `OPERA_Grupo LATAM` | LATAM group |
| `MES_12` | December — high season |
| `TIPOVUELO_I` | International flight |
| `MES_4` | April |
| `MES_11` | November |
| `OPERA_Sky Airline` | Low-cost carrier |
| `OPERA_Copa Air` | Copa Airlines |

### Class Balancing

The dataset is imbalanced (~85% no delay, ~15% delay). Without balancing, the model predicts nearly everything as class 0.

- **Technique:** `scale_pos_weight = n_y0 / n_y1`
- **Impact:** Recall for delay class improves from ~0.30 to >0.60

### Type Hints & Practices

- `ClassVar[List[str]]` for class-level constants (`FEATURES_COLS`, `ALL_OPERA`)
- `Optional[xgb.XGBClassifier]` for the model instance
- `Union[Tuple[pd.DataFrame, pd.DataFrame], pd.DataFrame]` for polymorphic `preprocess()` return

### Running Model Tests

```bash
make model-test
```

---

## 3. Part II — API (`challenge/api.py`)

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check — returns `{"status": "OK"}` |
| `/predict` | POST | Predict delay probability for a batch of flights |

### Request / Response Format

**Request:**
```json
{
  "flights": [
    {
      "OPERA": "Grupo LATAM",
      "TIPOVUELO": "I",
      "MES": 7
    }
  ]
}
```

**Response:**
```json
{
  "predict": [1]
}
```

### Validation

Pydantic v2 `Flight` model validates:
- `OPERA`: must be one of 16 airlines from the dataset
- `TIPOVUELO`: must be `"I"` (International) or `"N"` (National)
- `MES`: integer 1–12

### Lazy Model Loading

The model is loaded as a singleton on the first `/predict` request:

```python
_model: Any = None

def load_model() -> Any:
    if _model is not None:
        return _model
    # ... train on data.csv ...
    _model = model
    return _model
```

This avoids consuming memory at startup if the API is only used for health checks.

### Error Handling

- `400 Bad Request`: Validation errors (invalid airline, month, etc.)
- `500 Internal Server Error`: Unexpected prediction failures

### Running API Tests

```bash
make api-test
```

---

## 4. Part III — Deployment

### Cloud Provider: Google Cloud Platform (GCP)

- **Service:** Cloud Run (serverless containers)
- **Region:** `southamerica-east1` (São Paulo) — closest to LATAM operations, minimizes latency
- **Project:** `latam-flight-delay`

### Production URL

```
https://delay-model-api-chxpmithta-rj.a.run.app
```

### Quick Test

```bash
curl -X POST "https://delay-model-api-chxpmithta-rj.a.run.app/predict" \
  -H "Content-Type: application/json" \
  -d '{"flights":[{"OPERA":"Grupo LATAM","TIPOVUELO":"I","MES":7}]}'
```

### Dockerfile

Key points for Cloud Run compatibility:

```dockerfile
FROM python:3.11-slim
WORKDIR /app

# ... install deps ...

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

Cloud Run injects `PORT=8080` automatically. The container **must** listen on this port.

### Local Development

```bash
# Build and run locally
docker build -t delay-model-api:local .
docker run -p 8001:8080 -e OPENROUTER_API_KEY=$OPENROUTER_API_KEY delay-model-api:local

# Or with docker-compose (hot-reload)
docker-compose up --build
```

### Stress Test

```bash
make stress-test
```

**Results (production):**
- 2,180 requests
- 0 failures
- ~75 RPS
- P95 latency: ~940ms

---

## 5. Part IV — CI/CD

### Workflows

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| CI | `.github/workflows/ci.yml` | Push to `main`/`develop`/`feature/**`, PRs | Run model, API, and AI insights tests |
| CD | `.github/workflows/cd.yml` | Push to `develop` | Deploy to Cloud Run, auto-merge to `main` |

### CI Pipeline (`ci.yml`)

```yaml
on:
  push:
    branches: [main, develop, 'feature/**']
  pull_request:
    branches: [main, develop]

jobs:
  test:
    steps:
      - Set up Python 3.11
      - Install dependencies
      - Run API tests
      - Run Model tests
      - Run AI insights tests
```

### CD Pipeline (`cd.yml`)

```yaml
on:
  push:
    branches: [develop]

permissions:
  contents: write

jobs:
  deploy:
    steps:
      - Checkout with fetch-depth: 0
      - Authenticate to GCP
      - Deploy to Cloud Run: gcloud run deploy --source .
      - If success: git merge develop → main
```

### GitFlow Integration

- **develop:** Integration branch. All feature branches merge here.
- **main:** Release branch. Updated automatically by CD after successful deploy.
- **Feature branches:** `feature/*` — CI runs on push.

This satisfies the challenge requirement: "*It is highly recommended to use GitFlow development practices.*"

### CI/CD Optimization: `paths-ignore`

To avoid unnecessary deployments when only documentation changes are made, the workflows include `paths-ignore` for files that do not affect the application behavior:

```yaml
on:
  push:
    branches: [develop]
    paths-ignore:
      - 'docs/**'
      - '*.md'
      - 'README*'
      - 'LICENSE'
      - '.gitignore'
```

| Change Type | CI | CD |
|-------------|----|----|
| Only `docs/*.md` | ❌ Skip | ❌ Skip |
| Only `README.md` | ❌ Skip | ❌ Skip |
| `api.py` + `README.md` | ✅ Runs | ✅ Runs |

### GitHub Secrets Required

| Secret | Value | Purpose |
|--------|-------|---------|
| `GCP_PROJECT_ID` | `latam-flight-delay` | GCP project identifier |
| `GCP_REGION` | `southamerica-east1` | Deployment region |
| `GCP_SA_KEY` | JSON key of `github-actions` SA | GCP authentication |
| `OPENROUTER_API_KEY` | OpenRouter API key | LLM access for `/ai-insights` |

### IAM Roles Configured

| Service Account | Role | Resource |
|-----------------|------|----------|
| `github-actions@...` | `run.admin`, `cloudbuild.builds.builder`, `artifactregistry.writer` | Project |
| `github-actions@...` | `artifactregistry.writer` | Repo `cloud-run-source-deploy` |
| `32555940559@cloudbuild.gserviceaccount.com` | `run.admin`, `artifactregistry.writer` | Project + Repo |

---

## 6. Additional Enhancements (Bonus)

> **Note:** These features were not explicitly required by the challenge. They were added to demonstrate full-stack capabilities and the integration of LLMs with structured data, aligning with the **ML & LLMs** role focus.

### 6.1 React UI — SCL Flight Delay Predictor

**Motivation:** Provide a visual interface for airport staff to interact with the model without using `curl`.

**Stack:**
- Vite (build tool)
- React 19
- Tailwind CSS (styling)
- Lucide React (icons)

**Features:**
- **Dark mode** with LATAM branding (`#0f0f0f` background, `#CC0000` accent)
- **Responsive layout:** mobile (stack) / desktop (2-column grid)
- **Flight prediction form:** dropdowns for airline, type, month
- **SCL Insights chatbot:** conversational interface for data analysis

**Architecture:**
```
┌──────────────────────┐    ┌──────────────────────┐
│     FlightForm        │    │   SCL Insights       │
│  (Predict delays)     │    │   (Chat with data)   │
└──────────────────────┘    └──────────────────────┘
           │                           │
           └───────────┬───────────────┘
                       ▼
            ┌─────────────────────┐
            │   FastAPI Backend   │
            │  /predict /ai-insights│
            └─────────────────────┘
```

**Production access:** The UI is served at the root URL `https://delay-model-api-chxpmithta-rj.a.run.app/`

### 6.2 AI Insights Endpoint (`/ai-insights`)

**Motivation:** Demonstrate how LLMs can analyze structured flight data and provide conversational insights.

**Architecture — RAG (Retrieval-Augmented Generation):**

```
User Question → Polars extracts stats from CSV → Build prompt with context → LLM (OpenRouter) → Response
```

**Optimization for Cloud Run Free Tier:**

The dataset has ~682k rows. Reading it on every request would:
- Consume ~200MB RAM
- Take 3–5 seconds
- Risk cold-start timeouts

**Solution:** Precompute context at build time.

```
Build Time (Dockerfile):
  data/data.csv → Polars aggregates stats → data/context.json (~50KB)

Request Time:
  data/context.json → load() → build_prompt() → LLM call
```

| Metric | On-demand Polars | Precomputed JSON |
|--------|-----------------|------------------|
| Request time | 3–5s | <1s |
| Memory peak | ~200MB | ~50KB |
| Cold-start impact | High | Minimal |

**Endpoint:**

```bash
POST /ai-insights
Content-Type: application/json

{
  "question": "¿Por qué se retrasan los vuelos en diciembre?"
}
```

**Example Response:**
```json
{
  "insight": "Diciembre es el segundo mes con mayor tasa de retrasos (31%). Esto se debe a la alta demanda de vuelos por temporada de verano y las condiciones climáticas variables en la zona sur de Sudamérica.",
  "context_used": {
    "total_flights": 682061,
    "delay_rate": 0.186
  }
}
```

### Submission

To submit the challenge, send a POST request to:

```bash
curl -X POST https://advana-challenge-check-api-cr-k4hdbggvoq-uc.a.run.app/software-engineer \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Nelson Acosta",
    "mail": "aliagenttucuman@gmail.com",
    "github_url": "https://github.com/aliagenttucuman-byte/latam-flight-delay.git",
    "api_url": "https://delay-model-api-chxpmithta-rj.a.run.app"
  }'
```

**Expected response:**
```json
{
  "status": "OK",
  "detail": "your request was received"
}
```

**Please send only once.**
