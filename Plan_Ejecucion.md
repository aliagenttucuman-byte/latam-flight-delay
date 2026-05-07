# Plan de Ejecución - Desafío ML & LLMs LAN LATAM

## Resumen del Proyecto

El objetivo es operacionalizar un modelo de predicción de retrasos de vuelos del aeropuerto SCL, desplegándolo como API con CI/CD.

## Análisis de Archivos Clave

### Modelo (model.py)
- Estado: **COMPLETO** - XGBoost con top 10 features y class balancing
- Implementación: `_create_features()`, `preprocess()`, `fit()`, `predict()`
- Features: `["OPERA_Latin American Wings", "MES_7", "MES_10", "OPERA_Grupo LATAM", "MES_12", "TIPOVUELO_I", "MES_4", "MES_11", "OPERA_Sky Airline", "OPERA_Copa Air"]`
- Type hints: `ClassVar`, `Optional`, `Union`, `List`, `Dict`, `Any`

### API (api.py)
- Estado: **COMPLETO** - endpoint `/predict` implementado con validación
- Validación: `OPERA` (16aerolíneas conocidas), `TIPOVUELO` (I/N), `MES` (1-12)
- Pydantic v2: usa `@field_validator` (actualizado de `@validator` en upgrade 2026-05-06)
- Lazy loading del modelo con singleton pattern

### CI/CD (.github/workflows/)
- Estado: **EN PROGRESO** - Workflows definidos, necesitan completarse con credenciales GCP
- ci.yml:触发 push a develop/main, corre `make model-test` y `make api-test`
- cd.yml:触发 push a main, despliega a GCP Cloud Run
- Requiere: GitHub Secrets (`GCP_PROJECT_ID`, `GCP_REGION`, `GCP_SA_KEY`)

---

### FASE 0: Configuración de GCP (Cuenta Gratuita - aliagenttucuman@gmail.com)

**Importante:** Usar siempre la región `southamerica-east1` (São Paulo) para evitar costos de red entre regiones.

---

## 0.0.1 Checklist de Configuración GCP

Estado actual (actualizado durante sesión):

| Paso | Descripción | Estado | Notas |
|------|-------------|--------|-------|
| 0.1 | Crear proyecto `latam-flight-delay` | ✅listo | - |
| 0.2 | Habilitar APIs (run, containerregistry, cloudbuild) | ✅listo | - |
| 0.3 | Configurar región `southamerica-east1` | ✅listo | Configurado via CLI |
| 0.5 | Crear Service Account `github-actions` | ✅listo | Roles: run.admin, iam.serviceAccountUser, storage.objectViewer |
| 0.6 | Generar clave JSON | ✅listo | Guardada en `C:\temp\gcp-keys\key.json` |
| 0.7 | Configurar GitHub Secrets | ✅listo | 3 secrets configurados (GCP_PROJECT_ID, GCP_REGION, GCP_SA_KEY) |
| 0.8 | Crear `.github/workflows/` | ✅listo | Archivos ci.yml y cd.yml creados |

**Nota:** Los pasos 0.7 son prerequisitos para que `cd.yml` funcione.

---

## 0.0 Software Requerido (Instalar desde CLI)

Todo se puede hacer 100% desde línea de comandos. Instalar en orden:

### 0.0.1 Git (para GitHub)
```powershell
# Verificar si ya está instalado
git --version

# Si no está, instalar con winget (Windows)
winget install Git.Git
```

### 0.0.2 Docker Desktop (para construir imágenes)
```powershell
# Descargar e instalar Docker Desktop
# https://www.docker.com/products/docker-desktop/

# Verificar después de instalar
docker --version

# IMPORTANTE: Asegurarse que Docker Desktop esté corriendo (icono en barra)
# Sino, iniciar manualmente desde menú Inicio
```

### 0.0.3 Google Cloud SDK (gcloud CLI)
```powershell
# Opción 1: PowerShell installer (recomendado)
irm https://cloud.google.com/sdk/docs/install.ps1 | iex

# Opción 2: Installer manual
Invoke-WebRequest -Uri https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe -OutFile 'C:\temp\googlesdk.exe'
Start-Process -FilePath 'C:\temp\googlesdk.exe' -Wait

# Opción 3: Via winget
winget install GoogleCloudSDK

# Reiniciar terminal después de instalar

# Verificar instalación
gcloud --version
```

### 0.0.4 Python 3.11+ (para ejecutar localmente)
```powershell
# Verificar
python --version

# Si no está, instalar con winget
winget install Python.Python.3.11
```

---

## 0.1 Crear Proyecto GCP (100% CLI)

```powershell
# Autenticar con cuenta Google (abre navegador)
gcloud auth login

# Crear nuevo proyecto
gcloud projects create latam-flight-delay --name="Latam Flight Delay Challenge"

# Configurar como proyecto default
gcloud config set project latam-flight-delay

# Verificar
gcloud projects describe latam-flight-delay
```

**Alternativa visual:** Ir a https://console.cloud.google.com/projectcreate

---

## 0.2 Habilitar APIs necesarias (CLI)

```powershell
# Habilitar todas las APIs necesarias de una vez
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com

# Verificar que estén habilitadas
gcloud services list --enabled
```

**Alternativa visual:** console.cloud.google.com > APIs & Services > Library

---

## 0.3 Configurar región default

```powershell
# Configurar región (São Paulo - más económica para Latinoamérica)
gcloud config set region southamerica-east1

# Configurar zona
gcloud config set zone southamerica-east1-a

# Ver configuración
gcloud config list
```

---

## 0.4 Configurar Docker para GCP Container Registry

```powershell
# Autenticar Docker con GCP
gcloud auth configure-docker southamerica-east1-docker.pkg.dev

# Verificar (debe mostrar el registry)
docker search southamerica-east1-docker.pkg.dev/latam-flight-delay 2>$null
```

**Nota:** Esto permite hacer `docker push southamerica-east1-docker.pkg.dev/latam-flight-delay/...`

---

## 0.5 Crear Service Account para GitHub Actions (CLI)

```powershell
# Crear service account
gcloud iam service-accounts create github-actions `
  --project=latam-flight-delay `
  --display-name="GitHub Actions Deploy"

# Asignar rol Cloud Run Admin (permite desplegar)
gcloud projects add-iam-policy-binding latam-flight-delay `
  --member="serviceAccount:github-actions@latam-flight-delay.iam.gserviceaccount.com" `
  --role="roles/run.admin"

# Asignar rol Service Account User (para ejecutar como service account)
gcloud projects add-iam-policy-binding latam-flight-delay `
  --member="serviceAccount:github-actions@latam-flight-delay.iam.gserviceaccount.com" `
  --role="roles/iam.serviceAccountUser"

# Asignar rol Storage Object Viewer (para leer Container Registry)
gcloud projects add-iam-policy-binding latam-flight-delay `
  --member="serviceAccount:github-actions@latam-flight-delay.iam.gserviceaccount.com" `
  --role="roles/storage.objectViewer"

# Verificar service account creada
gcloud iam service-accounts list --project=latam-flight-delay
```

---

## 0.6 Generar Clave JSON para GitHub Secrets (CLI)

```powershell
# Crear directorio para guardar claves
New-Item -ItemType Directory -Path C:\temp\gcp-keys -Force

# Generar clave JSON (descarga archivo con credenciales)
gcloud iam service-accounts keys create C:\temp\gcp-keys\key.json `
  --iam-account=github-actions@latam-flight-delay.iam.gserviceaccount.com

# Ver contenido (copiar todo este contenido para GitHub Secret)
Get-Content C:\temp\gcp-keys\key.json

# ADVERTENCIA: No guardar esta clave en Git ni perderla
# Es una credencial sensible
```

**Nota:** Si necesitas regenerar la clave en el futuro:
```powershell
gcloud iam service-accounts keys delete KEY_ID --iam-account=github-actions@latam-flight-delay.iam.gserviceaccount.com
```

---

## 0.7 Configurar GitHub Secrets

1. En GitHub, ir al repositorio > **Settings** > **Secrets and variables** > **Actions**
2. Click **"New repository secret"** para cada uno:

| Secret Name | Value (copiar de key.json) |
|-------------|----------------------------|
| `GCP_SA_KEY` | Contenido completo del archivo `C:\temp\gcp-keys\key.json` |
| `GCP_PROJECT_ID` | `latam-flight-delay` |
| `GCP_REGION` | `southamerica-east1` |

**Verificación por CLI:**
```powershell
# En GitHub puedes verificar secrets configurados (solo nombres, no valores)
gh secret list
```

---

## 0.8 Verificar Configuración Completa (CLI)

```powershell
# 1. Ver servicios habilitados
gcloud services list --enabled

# 2. Ver configuración de gcloud
gcloud config list

# 3. Ver service accounts
gcloud iam service-accounts list --project=latam-flight-delay

# 4. Ver proyectos disponibles
gcloud projects list

# 5. Ver regiones disponibles
gcloud compute regions list

# 6. Ver configuración de Docker
docker-credential-gcloud configure list
```

Si todo está correcto, deberías ver:
- `run.googleapis.com` en la lista de servicios
- `github-actions@latam-flight-delay.iam.gserviceaccount.com` en service accounts
- `southamerica-east1` como región default

---

## 0.9 Comandos Rápidos de Verificación

```powershell
# Ver estado del proyecto
gcloud projects describe latam-flight-delay --format="table(name,project_number)"

# Ver APIs habilitadas
gcloud services list --enabled --format="table(config.title,config.name)"

# Ver políticas IAM del proyecto
gcloud projects get-iam-policy latam-flight-delay

# Ver containers en registry (si ya subiste alguno)
gcloud container images list-repository-urls
```

---

## Resumen: Alternativa 100% CLI vs Visual

| Tarea | CLI | Visual |
|-------|-----|--------|
| Crear proyecto | `gcloud projects create` | console.cloud.google.com |
| Habilitar APIs | `gcloud services enable` | Library > API > Enable |
| Crear Service Account | `gcloud iam service-accounts create` | IAM > Service Accounts |
| Asignar permisos | `gcloud projects add-iam-policy-binding` | IAM > Roles |
| Generar clave | `gcloud iam service-accounts keys create` | Service Account > Keys |
| Configurar GitHub Secrets | Manual (no CLI disponible) | GitHub Settings |

**Conclusión:** Todo EXCEPTO configurar GitHub Secrets se puede hacer 100% desde CLI.

---

## 0.10 Límites de Cuenta Gratuita (Always Free)

| Recurso | Límite | Uso en este proyecto |
|---------|--------|---------------------|
| Cloud Run | 2M requests/mes, 180K vCPU-seg/mes | API desplegada |
| Cloud Build | 120 min/día | CI/CD |
| Container Registry | 5GB | Almacenar imagen Docker |
| Compute Engine | 1 e2-micro (no usar) | N/A |

**Estrategia de costos:** Usar Cloud Run en vez de VMs. El tier gratuito cubre la carga de este proyecto.

---

**Ir a FASE 1:** Una vez completada esta fase, continuar con la implementación del código.

---

---

## Pasos de Ejecución

### FASE 1: Repositorio y Configuración Inicial

1. **Crear repositorio GitHub público**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<user>/<repo>.git
   git push -u origin main
   ```

2. **Crear rama develop para trabajo**
   ```bash
   git checkout -b develop
   ```

3. **Instalar dependencias localmente**
   ```bash
   make venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   make install
   ```

---

### FASE 1.5: Desarrollo Local con Docker

1. **Completar `Dockerfile`** (usar Python 3.11 slim para producción)
   ```dockerfile
   # syntax=docker/dockerfile:1.2
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY challenge/ ./challenge/
   COPY data/ ./data/

   ENV PYTHONUNBUFFERED=1

   EXPOSE 8000

   CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Crear `docker-compose.yml`** (para desarrollo con hot-reload)
   ```yaml
   version: '3.8'
   services:
     api:
       build: .
       ports:
         - "8000:8000"
       volumes:
         - .:/app
       environment:
         - PYTHONUNBUFFERED=1
       command: uvicorn challenge.api:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Comandos Docker para desarrollo local**
   ```bash
   # Construcción inicial
   docker build -t delay-model-api:local .

   # Ejecutar con docker-compose (con hot-reload)
   docker-compose up --build

   # Solo ejecutar (sin rebuild)
   docker-compose up

   # Ejecutar imagen directamente
   docker run -p 8000:8000 delay-model-api:local

   # Probar endpoints
   curl http://localhost:8000/health
   curl -X POST http://localhost:8000/predict \
     -H "Content-Type: application/json" \
     -d '{"flights":[{"OPERA":"Aerolineas Argentinas","TIPOVUELO":"N","MES":3}]}'

   # Ejecutar tests dentro del contenedor
   docker run --rm delay-model-api:local pytest tests/
   ```

4. **Verificar que Docker está corriendo**
   ```powershell
   docker --version
   docker ps  # Debe correr sin errores
   ```

---

### FASE 2: Implementación del Modelo (Parte I)

4. **Implementar `challenge/model.py`**

   Implementación completa con type hints senior (Python 3.11+):
   ```python
   from __future__ import annotations

   from typing import ClassVar, Optional, Tuple, List, Dict, Any, Union
   import pandas as pd
   import xgboost as xgb
   import numpy as np


   class DelayModel:
       """XGBoost model for flight delay prediction with class balancing.

       The model uses the top 10 features identified in the exploration notebook:
       - OPERA: Latin American Wings, Grupo LATAM, Sky Airline, Copa Air
       - MES: 4, 7, 10, 11, 12
       - TIPOVUELO: I (International)

       Class balancing is applied via scale_pos_weight during training.
       """

       FEATURES_COLS: ClassVar[List[str]] = [
           "OPERA_Latin American Wings", "MES_7", "MES_10",
           "OPERA_Grupo LATAM", "MES_12", "TIPOVUELO_I",
           "MES_4", "MES_11", "OPERA_Sky Airline", "OPERA_Copa Air"
       ]

       ALL_OPERA: ClassVar[List[str]] = [
           "American Airlines", "Air France", "Aerolineas Argentinas",
           "Avianca", "British Airways", "Copa Air", "Delta Air",
           "Grupo LATAM", "Iberia", "JetSmart", "Korean Air",
           "LATAM", "Latin American Wings", "Lloyd Aereo Boliviano",
           "Sky Airline", "United Airlines"
       ]

       ALL_TIPOVUELO: ClassVar[List[str]] = ["I", "N"]
       ALL_MES: ClassVar[List[int]] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

       def __init__(self) -> None:
           self._model: Optional[xgb.XGBClassifier] = None

       def _create_features(self, data: pd.DataFrame) -> pd.DataFrame:
           """Create dummy features for OPERA, TIPOVUELO, and MES columns.

           Uses pd.get_dummies with prefix to match the feature names
           expected by the trained model.

           Args:
               data: DataFrame with OPERA, TIPOVUELO, MES columns

           Returns:
               DataFrame with dummy columns.
           """
           features_df = pd.DataFrame()

           for col, prefix in [("OPERA", "OPERA"), ("TIPOVUELO", "TIPOVUELO"), ("MES", "MES")]:
               if col in data.columns:
                   dummies = pd.get_dummies(data[col], prefix=prefix)
                   features_df = pd.concat([features_df, dummies], axis=1)

           return features_df

       def preprocess(
           self,
           data: pd.DataFrame,
           target_column: Optional[str] = None
       ) -> Union[Tuple[pd.DataFrame, pd.DataFrame], pd.DataFrame]:
           """Prepare raw data for training or serving.

           Creates dummy variables from categorical columns (OPERA, TIPOVUELO, MES)
           using the complete dataset values to ensure consistent column structure.
           Then filters to keep only the top 10 FEATURES_COLS.

           Training mode (target_column provided):
               - Returns (features, target)

           Serving mode (target_column not provided):
               - Returns features only

           Args:
               data: Raw flight data DataFrame with columns:
                   - OPERA: Airline name
                   - TIPOVUELO: Flight type (I=International, N=National)
                   - MES: Month (1-12)
                   - delay: Target variable (optional, only for training)
               target_column: If provided, returns (features, target).
                            Otherwise returns only features.

           Returns:
               Tuple of (features, target) DataFrames or just features DataFrame.

           Raises:
               ValueError: If required columns are missing.
           """
           required_cols = {"OPERA", "TIPOVUELO", "MES"}
           if not required_cols.issubset(data.columns):
               missing = required_cols - set(data.columns)
               raise ValueError(f"Missing required columns: {missing}")

           features = self._create_features(data)

           existing_features = [col for col in self.FEATURES_COLS if col in features.columns]
           features_filtered = features[existing_features]

           for col in self.FEATURES_COLS:
               if col not in features_filtered.columns:
                   features_filtered = features_filtered.assign(**{col: 0})

           features_filtered = features_filtered[self.FEATURES_COLS]

           if target_column:
               if target_column not in data.columns:
                   raise ValueError(f"Target column '{target_column}' not found in data")
               target = data[[target_column]].copy()
               return features_filtered, target

           return features_filtered

       def fit(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
           """Fit XGBoost model with class balancing via scale_pos_weight.

           Calculates scale_pos_weight = count(y=0) / count(y=1) to handle
           class imbalance in the binary target variable.

           Args:
               features: Preprocessed feature DataFrame with 10 columns
                        matching FEATURES_COLS.
               target: Binary target as DataFrame with single column 'delay'
                      (0=no delay, 1=delay).

           Raises:
               RuntimeError: If model is already fitted.
           """
           if self._model is not None:
               raise RuntimeError("Model already fitted. Create a new instance to retrain.")

           y = target.values.ravel()

           n_y0 = int(np.sum(y == 0))
           n_y1 = int(np.sum(y == 1))

           if n_y1 == 0:
               raise ValueError("Target has no positive samples (all zeros)")

           scale_pos_weight = n_y0 / n_y1

           self._model = xgb.XGBClassifier(
               random_state=42,
               learning_rate=0.01,
               scale_pos_weight=scale_pos_weight,
               use_label_encoder=False,
               eval_metric="logloss"
           )
           self._model.fit(features, y)

       def predict(self, features: pd.DataFrame) -> List[int]:
           """Predict delays for preprocessed features.

           Args:
               features: Preprocessed features DataFrame with columns
                        matching FEATURES_COLS.

           Returns:
               List of integer predictions (0=no delay, 1=delay).

           Raises:
               RuntimeError: If model has not been fitted.
           """
           if self._model is None:
               raise RuntimeError("Model not fitted. Call fit() before predict().")

           predictions = self._model.predict(features)
           return predictions.tolist()
   ```

5. **Ejecutar tests del modelo**
   ```bash
   make model-test
   ```

---

### FASE 3: Implementación de la API (Parte II)

6. **Implementar `challenge/api.py`**

   Implementación completa con type hints senior y Pydantic v2:
   ```python
   from __future__ import annotations

   from fastapi import FastAPI, HTTPException, status
   from fastapi.responses import JSONResponse
   from pydantic import BaseModel, Field, validator, ValidationError
   from typing import Annotated, List, Dict, Any

   import pandas as pd
   import numpy as np


   VALID_OPERAS: List[str] = [
       "American Airlines", "Air France", "Aerolineas Argentinas",
       "Avianca", "British Airways", "Copa Air", "Delta Air",
       "Grupo LATAM", "Iberia", "JetSmart", "Korean Air",
       "LATAM", "Latin American Wings", "Lloyd Aereo Boliviano",
       "Sky Airline", "United Airlines"
   ]

   VALID_TIPOVUELO: List[str] = ["I", "N"]
   VALID_MES: List[int] = list(range(1, 13))


   class Flight(BaseModel):
       """Flight data model with validation."""

       OPERA: Annotated[
           str,
           Field(
               min_length=1,
               max_length=100,
               description="Airline name (e.g., 'Aerolineas Argentinas', 'Grupo LATAM')"
           )
       ]
       TIPOVUELO: Annotated[
           str,
           Field(
               pattern="^[IN]$",
               description="Flight type: I=International, N=National"
           )
       ]
       MES: Annotated[
           int,
           Field(
               ge=1,
               le=12,
               description="Month of the year (1-12)"
           )
       ]

       @field_validator("OPERA")
       @classmethod
       def validate_opera(cls, v: str) -> str:
           if v not in VALID_OPERAS:
               raise ValueError(
                   f"Invalid OPERA '{v}'. Must be one of: {', '.join(sorted(VALID_OPERAS))}"
               )
           return v

       @field_validator("TIPOVUELO")
       @classmethod
       def validate_tipovuelo(cls, v: str) -> str:
           if v not in VALID_TIPOVUELO:
               raise ValueError(
                   f"Invalid TIPOVUELO '{v}'. Must be one of: {', '.join(VALID_TIPOVUELO)}"
               )
           return v

       @field_validator("MES")
       @classmethod
       def validate_mes(cls, v: int) -> int:
           if v not in VALID_MES:
               raise ValueError(
                   f"Invalid MES '{v}'. Must be one of: {', '.join(map(str, VALID_MES))}"
               )
           return v


   class FlightBatch(BaseModel):
       flights: List[Flight]


   app = FastAPI(
       title="Flight Delay Prediction API",
       description="API for predicting flight delays at SCL airport using XGBoost",
       version="1.0.0"
   )


   _model: Any = None


   def load_model() -> Any:
       """Load and fit the DelayModel on startup (lazy initialization)."""
       global _model

       if _model is not None:
           return _model

       from challenge.model import DelayModel

       model = DelayModel()

       data = pd.read_csv("data/data.csv")

       features, target = model.preprocess(data, target_column="delay")
       model.fit(features, target)

       _model = model
       return _model


   @app.get("/health")
   async def get_health() -> Dict[str, str]:
       """Health check endpoint."""
       return {"status": "OK"}


   @app.post(
       "/predict",
       response_model=Dict[str, List[int]],
       status_code=status.HTTP_200_OK,
       responses={
           400: {"description": "Validation error - invalid flight data"},
           500: {"description": "Internal server error during prediction"}
       }
   )
   async def predict(batch: FlightBatch) -> Dict[str, List[int]]:
       """Predict flight delays for a batch of flights.

       Args:
           batch: Batch of flights containing OPERA, TIPOVUELO, MES.

       Returns:
           Dict with 'predict' key containing list of predictions (0 or 1).

       Raises:
           HTTPException 400: If any flight data fails validation.
           HTTPException 500: If prediction fails.
       """
       try:
           model = load_model()

           flight_dicts = [
               {"OPERA": flight.OPERA, "TIPOVUELO": flight.TIPOVUELO, "MES": flight.MES}
               for flight in batch.flights
           ]
           flights_df = pd.DataFrame(flight_dicts)

           features = model.preprocess(flights_df)

           predictions = model.predict(features)

           return {"predict": predictions}

       except ValidationError as e:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail=f"Validation error: {str(e)}"
           )
       except ValueError as e:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail=f"Invalid data: {str(e)}"
           )
       except Exception as e:
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail=f"Prediction error: {str(e)}"
           )
   ```

7. **Ejecutar tests de la API**
   ```bash
   make api-test
   ```

---

### FASE 4: Despliegue en GCP (Parte III)

8. **Completar `Dockerfile`** (producción)
   ```dockerfile
   # syntax=docker/dockerfile:1.2
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY challenge/ ./challenge/
   COPY data/ ./data/

   ENV PYTHONUNBUFFERED=1

   EXPOSE 8000

   CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

9. **Construir y probar imagen Docker localmente**
   ```bash
   # Construir imagen
   docker build -t delay-model-api:local .

   # Ejecutar contenedor
   docker run -p 8000:8000 delay-model-api:local

   # Probar con curl
   curl http://localhost:8000/health
   # Respuesta esperada: {"status":"OK"}
   ```

10. **Desplegar a GCP Cloud Run**
    ```bash
    gcloud run deploy delay-model-api \
      --source . \
      --region southamerica-east1 \
      --platform managed \
      --allow-unauthenticated \
      --memory 512M \
      --cpu 1 \
      --timeout 60s \
      --concurrency 100
    ```
    Guardar la URL输出 (ejemplo: `https://delay-model-api-xxxxx-southamerica-east1.run.app`)

11. **Actualizar Makefile línea 26**
    ```makefile
    STRESS_URL = https://<tu-deployment-url>.run.app
    ```

12. **Ejecutar stress test**
    ```bash
    make stress-test
    ```

---

### FASE 5: CI/CD (Parte IV)

13. **Crear `.github/workflows/ci.yml`**
     ```yaml
     name: 'Continuous Integration'
     on:
       push:
         branches: [main, develop, 'feature/**']
       pull_request:
         branches: [main, develop]

     jobs:
       test:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v4
           - name: Set up Python
             uses: actions/setup-python@v5
             with:
               python-version: '3.11'
           - name: Install dependencies
             run: make install
           - name: Run model tests
             run: make model-test
           - name: Run API tests
             run: make api-test
     ```

14. **Crear `.github/workflows/cd.yml`**
     ```yaml
     name: 'Continuous Delivery'
     on:
       push:
         branches: [main]

     jobs:
       deploy:
         runs-on: ubuntu-latest
         steps:
           - uses: actions/checkout@v4
           - name: Set up Python
             uses: actions/setup-python@v5
             with:
               python-version: '3.11'
           - name: Authenticate to GCP
             uses: google-github-actions/auth@v2
             with:
               credentials_json: ${{ secrets.GCP_SA_KEY }}
           - name: Set up GCP
             run: |
               gcloud config set project ${{ secrets.GCP_PROJECT_ID }}
               gcloud services enable run.googleapis.com
           - name: Deploy to Cloud Run
             run: |
               gcloud run deploy delay-model-api \
                 --source . \
                 --region ${{ secrets.GCP_REGION }} \
                 --platform managed \
                 --allow-unauthenticated \
                 --memory 512M \
                 --cpu 1
           - name: Output URL
             run: echo "Deployed URL: $(gcloud run services describe delay-model-api --region ${{ secrets.GCP_REGION }} --format 'value(status.url)')"
     ```

---

### FASE 6: Documentación

15. **Completar `docs/challenge.md`**
    - Explicar decisiones del modelo
    - Documentar arquitectura de la API
    - Describir pipeline CI/CD
    - Incluir instrucciones de despliegue

16. **Commit final y push**
    ```bash
    git add .
    git commit -m "Challenge completo"
    git push origin develop
    git push origin main
    ```

---

### FASE 7: Envío

17. **Enviar POST request**
    ```bash
    curl -X POST https://advana-challenge-check-api-cr-k4hdbggvoq-uc.a.run.app/software-engineer \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Tu Nombre",
        "mail": "tu@email.com",
        "github_url": "https://github.com/<user>/<repo>.git",
        "api_url": "https://<deployment-url>.run.app"
      }'
    ```

---

### FASE 8: Push a GitHub y Deployment

> **Nota:** Esta fase se ejecuta MANUALMENTE por el desarrollador. No es automatizada por CI/CD.

#### STEP_A: Mover workflows a .github/

El README.md línea 120 indica copiar la carpeta `workflows/` dentro de `.github/`. Ejecutar:

```powershell
# 1. Crear estructura de carpetas
New-Item -ItemType Directory -Path ".github\workflows" -Force

# 2. Copiar archivos (sobrescribir si ya existen)
Copy-Item -Path "workflows\ci.yml" -Destination ".github\workflows\ci.yml" -Force
Copy-Item -Path "workflows\cd.yml" -Destination ".github\workflows\cd.yml" -Force
```

**Verificar:**
```powershell
Get-ChildItem -Path ".github\workflows" -File
```
Debe mostrar `ci.yml` y `cd.yml`.

---

#### STEP_B: Configurar GitHub Secrets

**Desde la web de GitHub:**

1. Ir a `https://github.com/aliagenttucuman-byte/latam-flight-delay/settings/secrets/actions`
2. Click **"New repository secret"** para cada uno:

| Secret Name | Valor | Descripción |
|-------------|-------|-------------|
| `GCP_PROJECT_ID` | `latam-flight-delay` | ID del proyecto GCP |
| `GCP_REGION` | `southamerica-east1` | Región de GCP (São Paulo) |
| `GCP_SA_KEY` | *(JSON del service account)* | Credenciales del SA `github-actions` |

**Para obtener GCP_SA_KEY:**
```bash
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@latam-flight-delay.iam.gserviceaccount.com

# Copiar el contenido de key.json como valor del secret
```

---

#### STEP_C: Inicializar Git y Push

```powershell
# 1. Ir al directorio del proyecto
cd "C:\Users\NelsonAcosta\.gemini\antigravity\scratch\Examen_LAN_LATAM"

# 2. Si git no está iniciado, inicializar
git init

# 3. Agregar todos los archivos (incluye .github/ y excluye __pycache__, .pytest_cache, etc)
git add .

# 4. Commit inicial
git commit -m "Initial commit: Flight Delay Prediction API with XGBoost"

# 5. Crear rama main y develop
git branch -M main
git branch develop

# 6. Agregar remote (si no existe)
git remote add origin https://github.com/aliagenttucuman-byte/latam-flight-delay.git

# 7. Push a main
git push -u origin main

# 8. Push a develop
git push -u origin develop
```

**Verificar en GitHub:**
- Ir a `https://github.com/aliagenttucuman-byte/latam-flight-delay`
- Verificar que aparecen `.github/workflows/ci.yml` y `cd.yml`

---

#### STEP_D: Primer Deploy Manual a GCP (si cd.yml falla)

```bash
# Autenticarse con GCP
gcloud auth login

# Configurar proyecto
gcloud config set project latam-flight-delay

# Desplegar
gcloud run deploy delay-model-api \
  --source . \
  --region southamerica-east1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512M \
  --cpu 1

# Obtener URL del servicio
gcloud run services describe delay-model-api \
  --region southamerica-east1 \
  --format "value(status.url)"
```

**Actualizar Makefile línea 26:**
```powershell
# Editar Makefile línea 26
# Cambiar: STRESS_URL = http://127.0.0.1:8000
# Por: STRESS_URL = https://delay-model-api-XXXXXXXX-southamerica-east1.run.app
```

---

#### STEP_E: Enviar POST Request Final

```bash
curl -X POST https://advana-challenge-check-api-cr-k4hdbggvoq-uc.a.run.app/software-engineer \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tu Nombre",
    "mail": "aliagenttucuman@gmail.com",
    "github_url": "https://github.com/aliagenttucuman-byte/latam-flight-delay.git",
    "api_url": "https://delay-model-api-XXXXXXXX-southamerica-east1.run.app"
  }'
```

---

## Notas sobre Restricciones del README Original

El desafio original tenía las siguientes restricciones que fueron respetadas:

| Restricción | Cumplimiento |
|-------------|--------------|
| No cambiar estructura del challenge | ✅ Estructura de carpetas/archivos intacta |
| No cambiar nombres/argumentos de métodos | ✅ `DelayModel.preprocess()`, `fit()`, `predict()` intactos |
| No usar otro framework | ✅ Solo FastAPI |
| Métodos pueden completarse | ✅ Implementación completa agregada |
| Métodos extras permitidos | ✅ `_create_features()`, `_calculate_delay()` creados |
| URL de API en Makefile línea 26 | ⏳ Pendiente (se actualiza tras deploy) |
| Documentación en docs/challenge.md | ⚠️ La documentación técnica está en este Plan_Ejecucion.md como referencia de desarrollo. El archivo `docs/challenge.md` puede contener el resumen ejecutivo. |

---

## Instrucciones de Ejecución de Tests

### Model Tests (desde tests/model)

```bash
cd tests/model
python -m pytest test_model.py -v
cd ../..
```

**Nota:** Estos tests usan path relativo `../data/data.csv`, por eso deben ejecutarse desde `tests/model/`.

### API Tests (desde raíz del proyecto)

```bash
python -m pytest tests/api/test_api.py -v
```

### Todos los Tests

```bash
# API tests desde raíz
python -m pytest tests/api/test_api.py -v

# Model tests desde tests/model
cd tests/model && python -m pytest test_model.py -v && cd ../..
```

### Desarrollo Local de la API

```bash
cd C:\path\to\project
uvicorn challenge.api:app --reload --host 0.0.0.0 --port 8000
```

Probar:
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"flights":[{"OPERA":"Aerolineas Argentinas","TIPOVUELO":"N","MES":3}]}'
```

---

## Decisiones de Diseño

### Modelo: XGBoost con Class Balancing

| Decisión | Justificación |
|----------|---------------|
| **XGBoost** | Según el notebook, XGBoost y Logistic Regression mostraban resultados similares. Se eligió XGBoost por su mejor manejo de features categóricas y mayor robustez a overfitting. |
| **Top 10 Features** | Reducir de ~50+ features a 10 principales mejora la velocidad de inferencia sin degradar significativamente el recall de la clase positiva (requirement: recall > 0.60 para clase 1). |
| **Class Balancing (scale_pos_weight)** | El dataset está desbalanceado (~85% no delay, ~15% delay). Sin balancing, el modelo predice casi todo como clase 0. Con `scale_pos_weight = n_y0/n_y1` el recall de clase 1 pasa de ~0.3 a >0.6. |
| **get_dummies interno** | No se usa `get_dummies` directamente en la API para evitar crear columnas no necesarias. El método `_create_features()` genera las dummies internamente y luego se filtra por `FEATURES_COLS`. |

### API: FastAPI con Pydantic v2

| Decisión | Justificación |
|----------|---------------|
| **FastAPI** | Requirement del desafío (no se puede usar otro framework). Soporta async nativamente y tiene validación de schemas integrada. |
| **Pydantic v2 con Annotated** | `Annotated` + `Field` permite documentar los campos y validar con expresiones regulares (`pattern="^[IN]$"`) de forma declarativa. |
| **Lazy Loading del modelo** | El modelo se carga una sola vez en `_model` global. Se entrena al primer request `/predict` para no consumir memoria en startup si no se necesita. |
| **Validación de 16 aerolíneas** | Se validan TODAS las categorías del dataset, no solo las 4 que aparecen en `FEATURES_COLS`. Esto evita que inputs inválidos generen features incorrectas. |

### Type Hints Senior (Python 3.11+)

| Type Hint | Uso en el Código |
|-----------|------------------|
| `ClassVar[List[str]]` | Define constantes de clase como `FEATURES_COLS`, `ALL_OPERA`, `VALID_OPERAS` que no son instancias sino de la clase misma. |
| `Optional[str]` | Parámetros que pueden ser `None` (ej: `target_column: Optional[str] = None`). |
| `Union[Tuple[...], ...]` | Return type polimórfico: `preprocess()` retorna `(features, target)` o solo `features`. |
| `Annotated[str, Field(...)]` | Pydantic v2: combina el tipo base con metadata de validación y documentación. |
| `Dict[str, List[int]]` | Response model explícito para el endpoint `/predict`. |
| `Any` | Para el modelo singleton global (`_model: Any = None`) ya que el tipo exacto depende de runtime. |

---

## Arquitectura de la API

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                               │
│  POST /predict                                                      │
│  { "flights": [{"OPERA": "...", "TIPOVUELO": "I", "MES": 7}] }      │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Validation Layer                          │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  Flight Schema (Pydantic v2)                                │     │
│  │  ├── OPERA: Valida contra VALID_OPERAS (16 airlines)        │     │
│  │  ├── TIPOVUELO: pattern "^[IN]$" (I=International, N=Nat)   │     │
│  │  └── MES: ge=1, le=12                                       │     │
│  └─────────────────────────────────────────────────────────────┘     │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ ValidationError → HTTP 400
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     load_model() - Lazy Singleton                    │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │  if _model is None:                                         │     │
│  │      model = DelayModel()                                   │     │
│  │      data = pd.read_csv("data/data.csv")                    │     │
│  │      features, target = model.preprocess(data,             │     │
│  │                              target_column="delay")         │     │
│  │      model.fit(features, target)                            │     │
│  │      _model = model                                         │     │
│  └─────────────────────────────────────────────────────────────┘     │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Prediction Pipeline                              │
│  1. Convert Flight → DataFrame                                       │
│  2. model.preprocess(flights_df) → features (top 10 cols)           │
│  3. model.predict(features) → List[int]                            │
│  4. Return {"predict": [0, 1, 0, ...]}                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Glosario de Type Hints

| Type Hint | Significado | Ejemplo |
|-----------|-------------|---------|
| `int` | Entero | `age: int = 25` |
| `float` | Decimal | `rate: float = 0.85` |
| `str` | String | `name: str = "Latam"` |
| `bool` | Booleano | `is_active: bool = True` |
| `list[int]` | Lista de enteros | `ids: list[int] = [1, 2, 3]` |
| `dict[str, int]` | Dict string→int | `counts: dict[str, int] = {"a": 1}` |
| `tuple[int, str]` | Tupla fija | `pair: tuple[int, str] = (1, "a")` |
| `Optional[int]` | int o None | `age: Optional[int] = None` |
| `Union[int, str]` | int o str | `val: Union[int, str] = 1` |
| `List[int]` | Lista (forma moderna) | `items: List[int] = [1, 2]` |
| `Dict[str, Any]` | Dict con valores mixtos | `data: Dict[str, Any] = {}` |
| `ClassVar[List[str]]` | Variable de clase, no de instancia | `FEATURES_COLS: ClassVar[List[str]]` |
| `Tuple[int, ...]` | Tupla de longitud variable | `coords: Tuple[int, ...] = (1, 2, 3)` |
| `Literal["I", "N"]` | Valor exacto permitido | `tipo: Literal["I", "N"] = "I"` |
| `Annotated[x, Field()]` | Tipo con metadata extra | `OPERA: Annotated[str, Field(...)]` |
| `Callable[[int], str]` | Función que recibe int y retorna str | `func: Callable[[int], str]` |
| `Iterator[int]` | Iterador de enteros | `it: Iterator[int]` |
| `Generator[int, None, None]` | Generador de enteros | `gen: Generator[int, None, None]` |

---

## Historial de Cambios

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-05-05 | 1.0.0 | Versión inicial del plan |
| 2026-05-05 | 1.1.0 | Agregada FASE 1.5 (Docker local), Python 3.11+ |
| 2026-05-05 | 1.2.0 | Código completo model.py con type hints senior |
| 2026-05-05 | 1.3.0 | Código completo api.py con Pydantic v2 |
| 2026-05-05 | 1.4.0 | Agregadas secciones: Decisiones de Diseño, Arquitectura, Glosario, Changelog |
| 2026-05-05 | 1.5.0 | Actualización de dependencias (numpy 1.22.4→1.23.0, pandas 1.3.5→1.5.0), añadido xgboost al requirements.txt. Corrección Pydantic: field_validator→validator para compatibilidad con v1.10.2. |

---

## Cambios Realizados vs Original

Cada archivo modificado tiene comentarios inline referenciando este documento. Esto permite auditar los cambios y justifica las decisiones tomadas.

### Mapeo de Cambios

| Archivo | Cambio | Justificación README | Referencia Inline |
|---------|--------|----------------------|-------------------|
| `requirements.txt` | numpy 1.22.4→1.23.0, pandas 1.3.5→1.5.0, +xgboost | "create extra classes and methods" + "apply all good programming practices" | Header comment referencing Plan_Ejecucion.md |
| `Dockerfile` | Completado (estaba vacío/inutilizable) | Requerido para hacer el challenge ejecutable | Header comment referencing Plan_Ejecucion.md |
| `docker-compose.yml` | Creado (no existía) | "create extra classes" para development flow | Header comment referencing Plan_Ejecucion.md |
| `challenge/api.py` | `field_validator`→`validator` | Compatibilidad con Pydantic 1.10.2 instalada | Header comment referencing Plan_Ejecucion.md |

### Principios Aplicados

1. **No cambiar estructura del challenge**: Carpetas, archivos, nombres de métodos intactos
2. **Decisiones documentadas**: Cada cambio tiene referencia al理由 en Plan_Ejecucion.md
3. **Reproducibilidad**: Los cambios de dependencias resuelven problemas de compilación en Python 3.11 sin cambiar lógica de negocio
4. **Justificación rastreable**: Los comentarios en el código permiten auditar por qué se hizo cada modificación

---

## Guía de Prueba Manual con Docker

### Construcción y ejecución

```powershell
# Construir imagen
docker build -t delay-model-api:local .

# Ejecutar contenedor (background)
docker run -d --name delay-api-test -p 8000:8000 delay-model-api:local

# Ver logs (esperar ~15s para que cargue el modelo)
docker logs delay-api-test --tail 20
```

### Pruebas manuales desde consola

```powershell
# 1. Health check
python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').read().decode())"
# Respuesta: {"status":"OK"}

# 2. Predicción con diferentes datos
python -c "
import urllib.request, json

# Caso 1: LATAM, International, Junio (mes 6)
data = json.dumps({'flights':[{'OPERA':'LATAM','TIPOVUELO':'I','MES':6}]}).encode()
req = urllib.request.Request('http://localhost:8000/predict', data=data, headers={'Content-Type':'application/json'})
print('LATAM+I+MES6:', urllib.request.urlopen(req).read().decode())

# Caso 2: Aerolineas Argentinas, National, Marzo (mes 3)
data = json.dumps({'flights':[{'OPERA':'Aerolineas Argentinas','TIPOVUELO':'N','MES':3}]}).encode()
req = urllib.request.Request('http://localhost:8000/predict', data=data, headers={'Content-Type':'application/json'})
print('Arg+N+MES3:', urllib.request.urlopen(req).read().decode())

# Caso 3: Copa Air, International, Diciembre (mes 12)
data = json.dumps({'flights':[{'OPERA':'Copa Air','TIPOVUELO':'I','MES':12}]}).encode()
req = urllib.request.Request('http://localhost:8000/predict', data=data, headers={'Content-Type':'application/json'})
print('Copa+I+MES12:', urllib.request.urlopen(req).read().decode())
"
```

### Datos de prueba sugeridos

| OPERA | TIPOVUELO | MES | Descripción |
|-------|-----------|-----|-------------|
| LATAM | I | 6 | Aerolínea principal, internacional, mes medio |
| Aerolineas Argentinas | N | 3 | Aerolínea argentina, nacional, inicio otoño |
| Copa Air | I | 12 | Aerolínea panameña, internacional, diciembre |
| Sky Airline | N | 7 | Low cost chilena, nacional, invierno |
| United Airlines | I | 10 | Internacional, octubre |

### Detener contenedor

```powershell
docker stop delay-api-test
docker rm delay-api-test
```

### Stress test (con Locust)

```powershell
# 50 usuarios, 30 segundos
python -m locust -f tests/stress/api_stress.py --print-stats --headless --users 50 --spawn-rate 5 -H http://localhost:8000 --run-time 30s
```

---

## Notas Importantes

1. **No cambiar estructura del desafío** - mantener nombres de archivos/carpetas
2. **Mantener métodos proporcionados** - no renombrar ni cambiar firmas de model.py
3. **API debe quedar desplegada** hasta revisión de stress tests
4. **Enviar aunque no esté completo** - dice "Recomendamos enviar el desafío incluso si no lograste terminar todas las partes"
5. **Usar GitFlow** - no eliminar ramas de desarrollo

---

## Orden Sugerido de Ejecución

```
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 17
```

Cada fase depende de la anterior. La Fase 5 (CI/CD) puede desarrollarse en paralelo con otras.

---

## CD Deployment Errors Log (2026-05-06)

Errores encontrados durante el primer deploy a GCP Cloud Run desde GitHub Actions y sus soluciones.

### Error 1: YAML Syntax Error in cd.yml

**Mensaje:**
```
You have an error in your yaml syntax on line 34
Invalid workflow file
```

**Causa:** El step `Output URL` usaba `$(...)` dentro del `run:` block. GitHub Actions interpreta `$` como variable de template, no como shell.

**Fix aplicado en cd.yml:**
```yaml
# ANTES (error):
- name: Output URL
  run: echo "Deployed URL: $(gcloud run services describe...)"

# DESPUES (eliminado):
# Se removió el step problemático
```

**Lección:** No usar `$(...)` directamente en `run:` blocks de GitHub Actions. Usar `$$` para escapar o evitar estos commands.

---

### Error 2: SA Lacks Permission for `gcloud services enable`

**Mensaje:**
```
ERROR: (gcloud.services.enable) PERMISSION_DENIED: Permission denied to enable service [run.googleapis.com]
```

**Causa:** El SA `github-actions@latam-flight-delay.iam.gserviceaccount.com` no tenía rol para habilitar APIs.

**Fix:** Remover `gcloud services enable run.googleapis.com` del cd.yml. La API ya estaba habilitada desde la consola.

**Lección:** En cuentas gratuitas, las APIs ya pueden estar habilitadas. No es necesario habilitarlas en el workflow.

---

### Error 3: Artifact Registry Repository Does Not Exist

**Mensaje:**
```
Deploying from source requires an Artifact Registry Docker repository to store built containers.
A repository named [cloud-run-source-deploy] in region [***] will be created.
ERROR: (gcloud.run.deploy) PERMISSION_DENIED: The caller does not have permission.
```

**Causa:** El repo `cloud-run-source-deploy` no existía, y cuando GitHub Actions intentaba crearlo, fallaba por permisos.

**Fix:** Crear el repo manualmente desde CLI:
```bash
gcloud artifacts repositories create cloud-run-source-deploy \
  --repository-format=docker \
  --location=southamerica-east1 \
  --project=latam-flight-delay
```

**Lección:** `--source .` en `gcloud run deploy` necesita un Artifact Registry existente. Crearlo manualmente antes del primer deploy.

---

### Error 4: Cloud Build SA Lacked Artifact Registry Permissions

**Mensaje:**
```
ERROR: (gcloud.run.deploy) PERMISSION_DENIED: Permission 'artifactregistry.repositories.get' denied
on resource '//artifactregistry.googleapis.com/projects/***/locations/***/repositories/cloud-run-source-deploy'
```

**Causa:** `gcloud run deploy --source .` internamente usa Cloud Build para construir la imagen. El SA de Cloud Build (`32555940559@cloudbuild.gserviceaccount.com`) necesitaba permisos en el repo de Artifact Registry.

**Fix:**
```bash
# Permisos para Cloud Build SA en el repo
gcloud artifacts repositories add-iam-policy-binding cloud-run-source-deploy \
  --location=southamerica-east1 \
  --member="serviceAccount:32555940559@cloudbuild.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Permisos para Cloud Build SA en el proyecto
gcloud projects add-iam-policy-binding latam-flight-delay \
  --member="serviceAccount:32555940559@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"
```

**Lección:** Cuando se usa `--source .`, Cloud Build (no el SA de GitHub Actions) hace el build y push. Cloud Build necesita permisos tanto en Artifact Registry como en Cloud Run.

---

### Error 5: GitHub Actions SA Lacked `cloudbuild.builds.builder` Role

**Mensaje:**
```
ERROR: (gcloud.run.deploy) The caller does not have permission.
Authentication: github-actions@...iam.gserviceaccount.com
```

**Causa:** El SA de GitHub Actions también necesitaba el rol `cloudbuild.builds.builder` para poder crear Cloud Build jobs.

**Fix:**
```bash
gcloud projects add-iam-policy-binding latam-flight-delay \
  --member="serviceAccount:github-actions@latam-flight-delay.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"
```

**Lección:** Aunque el SA de GitHub Actions usa credenciales de Cloud Build internamente, necesita el rol `cloudbuild.builds.builder` para solicitar la construcción del contenedor.

---

### Error 6: Dockerfile Container Port Mismatch

**Mensaje:**
```
ERROR: The user-provided container failed to start and listen on the port defined provided
by the PORT=8080 environment variable within the allocated timeout.
```

**Causa:** Cloud Run define automáticamente `PORT=8080` y espera que el contenedor escuche en ese puerto. El Dockerfile usaba puerto 8000.

**Fix en Dockerfile:**
```dockerfile
# ANTES:
EXPOSE 8000
CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8000"]

# DESPUES:
EXPOSE 8080
ENV PORT=8080
CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Lección:** Cloud Run siempre inyecta `PORT=8080`. El contenedor DEBE escuchar en ese puerto.

---

## Resumen de Roles IAM Configurados

| Service Account | Recurso | Rol |
|----------------|---------|-----|
| `github-actions@...` | Proyecto | `artifactregistry.admin` |
| `github-actions@...` | Proyecto | `artifactregistry.writer` |
| `github-actions@...` | Proyecto | `cloudbuild.builds.builder` |
| `github-actions@...` | Proyecto | `iam.serviceAccountUser` |
| `github-actions@...` | Proyecto | `run.admin` |
| `github-actions@...` | Proyecto | `storage.objectViewer` |
| `github-actions@...` | Repo `cloud-run-source-deploy` | `artifactregistry.admin` |
| `github-actions@...` | Repo `cloud-run-source-deploy` | `artifactregistry.writer` |
| `32555940559@cloudbuild.gserviceaccount.com` | Repo `cloud-run-source-deploy` | `artifactregistry.writer` |
| `32555940559@cloudbuild.gserviceaccount.com` | Proyecto | `run.admin` |

---

## cd.yml Final (Working Version)

```yaml
name: 'Continuous Delivery'

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      - name: Set up GCP
        run: gcloud config set project ${{ secrets.GCP_PROJECT_ID }}
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy delay-model-api \
            --source . \
            --region ${{ secrets.GCP_REGION }} \
            --platform managed \
            --allow-unauthenticated \
            --memory 512M \
            --cpu 1
```

**Nota:** Se removió `gcloud services enable` y `Output URL` step para evitar errores de permisos y sintaxis.

---

## FASE 9: PoC AI Insights - RAG con Polars + MiniMax

### Resumen del Feature

Agregar un nuevo endpoint `/ai-insights` que usa IA generativa para analizar retrasos de vuelos. El flujo es un RAG simple:

```
User Question → Polars extrae stats del CSV → LLM (MiniMax via OpenRouter) → Respuesta conversacional
```

**Objetivo:** Demostrar cómo un LLM puede conversar con datos estructurados de vuelos, detectando patrones y generando insights.

---

### Arquitectura del Feature

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                               │
│  POST /ai-insights                                                    │
│  { "question": "¿Por qué se retrasan los vuelos en julio?" }         │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   challenge/ai_insights.py                            │
│                                                                      │
│  1. generate_context(csv_path) → Polars extrae stats del CSV         │
│  2. build_prompt(question, context) → Arma system + user prompt     │
│  3. call_llm(prompt) → Llama a MiniMax via OpenRouter               │
│  4. return {"insight": "..."}                                       │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    LLM (MiniMax 2.5 via OpenRouter)                  │
│                                                                      │
│  Model: claude-sonnet-4                                          │
│  API: https://opencode.ai/zen/v1/chat/completions                  │
│  System Role: "Data analyst expert, responds in Spanish"            │
│  Context: Stats extracted by Polars (delay rates, patterns, etc)     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### Arquitectura: Precomputed Context (Optimizado para GCP Free Tier)

**Problema:** GCP Cloud Run free tier tiene 1 vCPU y 512MB RAM. Leer 600k+ filas del CSV en cada request consumiría ~200MB+ de memoria y ~3-5 segundos de CPU, arriesgando cold start failures y memory spikes con requests simultáneos.

**Solución:** Generar el contexto UNA vez durante el build del contenedor, guardarlo como JSON estático, y cargarlo en request time (~1ms, ~50KB).

```
BUILD TIME (Dockerfile):
┌─────────────────────────────────────────────────────────────────────┐
│  data/data.csv (600k filas)                                         │
│         ↓                                                           │
│  Polars lee solo columnas necesarias (OPERA, TIPOVUELO, MES, delay)  │
│         ↓                                                           │
│  Genera estadísticas (16 airlines, 12 months, cross-analysis)        │
│         ↓                                                           │
│  Guarda data/context.json (~50KB)                                   │
└─────────────────────────────────────────────────────────────────────┘

REQUEST TIME (Cold Run):
┌─────────────────────────────────────────────────────────────────────┐
│  data/context.json (~50KB) → load() → context dict (~1ms)            │
│         ↓                                                           │
│  build_prompt() → LLM → response                                    │
└─────────────────────────────────────────────────────────────────────┘
```

**Beneficio:**
| Métrica | Polars on-demand | Precomputed JSON |
|---------|------------------|------------------|
| Request time | 3-5 segundos | <1 segundo |
| Memory peak | ~200MB | ~50KB |
| Cold start impact | Alto | Casi nulo |
| CPU GCP | Alto | Nulo |
| Concurrent requests | Problemas de memoria | Soporta bien |

---

### Archivos a Crear/Modificar

| Archivo | Cambio |
|---------|--------|
| `data/context.json` | NUEVO: Generado en build time, copiado al contenedor |
| `challenge/ai_insights.py` | NUEVO: `generate_and_save_context()` + `load_context()` |

---

### Nuenas Funciones para Build Time y Request Time

```python
def generate_and_save_context(
    csv_path: str = "data/data.csv",
    output_path: str = "data/context.json"
) -> None:
    """Genera contexto con Polars y lo guarda como JSON.

    Esta función DEBE ejecutarse durante el build del contenedor
    (Dockerfile RUN command). NO debe ejecutarse en request time.

    Args:
        csv_path: Path al CSV con datos de vuelos.
        output_path: Path donde guardar el JSON precomputado.
    """
    context = generate_context(csv_path)
    with open(output_path, "w") as f:
        json.dump(context, f, indent=2)


def load_context(json_path: str = "data/context.json") -> Dict[str, Any]:
    """Carga contexto precomputado desde JSON.

    Esta función es para request time. No usa Polars, solo lee el JSON.

    Args:
        json_path: Path al archivo JSON precomputado.

    Returns:
        Dict con el contexto cargado.
    """
    with open(json_path, "r") as f:
        return json.load(f)


# Contexto precomputado (cargado una vez, cacheado en memoria)
_context_cache: Optional[Dict[str, Any]] = None


def get_cached_context(json_path: str = "data/context.json") -> Dict[str, Any]:
    """Carga y cachea el contexto en memoria.

    Usa caching para evitar lecturas repetidas del archivo JSON
    en múltiples requests.

    Args:
        json_path: Path al archivo JSON precomputado.

    Returns:
        Dict con el contexto cargado.
    """
    global _context_cache
    if _context_cache is None:
        _context_cache = load_context(json_path)
    return _context_cache
```

---

### Implementación Paso a Paso

#### Paso 9.1: Crear `challenge/ai_insights.py`

```python
from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional

import httpx
import polars as pl


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "claude-sonnet-4"

SYSTEM_PROMPT = """Eres un analista de datos experto en retrasos de vuelos del aeropuerto SCL (Santiago de Chile).

DATASET:
- Fuente: data/data.csv (~682k vuelos históricos)
- Columnas principales:
  - OPERA: Nombre de aerolinea (16 válidas: American Airlines, Air France, Aerolineas Argentinas, Avianca, British Airways, Copa Air, Delta Air, Grupo LATAM, Iberia, JetSmart, Korean Air, LATAM, Latin American Wings, Lloyd Aereo Boliviano, Sky Airline, United Airlines)
  - TIPOVUELO: I=Internacional, N=Nacional
  - MES: Mes de operación (1-12)
  - Fecha-I: Fecha inicio (scheduled)
  - Fecha-O: Fecha operación (actual)
  - delay: Target binario (1 si Fecha-O - Fecha-I > 15 minutos, 0 si no)

TOP 10 FEATURES DEL MODELO XGBOOST:
- OPERA_Latin American Wings, MES_7, MES_10, OPERA_Grupo LATAM, MES_12, TIPOVUELO_I, MES_4, MES_11, OPERA_Sky Airline, OPERA_Copa Air

REGLAS:
1. Responde SIEMPRE en español
2. Usa números y estadísticas del contexto cuando estén disponibles
3. Si no tienes suficiente información, dilo claramente
4. Sé conciso pero informativo (máximo 3-4 oraciones para respuestas simples)
5. Para análisis complejos, usa bullet points
6. IMPORTANTE: Delay se define como >15 minutos de diferencia entre Fecha-O y Fecha-I
7. No especular sobre razones no respaldadas por los datos

Contexto de los datos:
{context}

Pregunta del usuario: {question}
"""


def generate_context(csv_path: str = "data/data.csv") -> Dict[str, Any]:
    """Extrae estadísticas relevantes del CSV usando Polars.

    Incluye stats para las 16 aerolineas, los 12 meses, y ambos tipos de vuelo.
    """
    df = pl.read_csv(csv_path, low_memory=False)

    total_flights = len(df)
    total_delays = df.filter(pl.col("delay") == 1).height
    delay_rate = total_delays / total_flights if total_flights > 0 else 0

    # ALL 16 airlines (sorted by name for consistency)
    all_airlines = [
        "American Airlines", "Air France", "Aerolineas Argentinas", "Avianca",
        "British Airways", "Copa Air", "Delta Air", "Grupo LATAM", "Iberia",
        "JetSmart", "Korean Air", "LATAM", "Latin American Wings",
        "Lloyd Aereo Boliviano", "Sky Airline", "United Airlines"
    ]

    # Delay by airline (ALL 16, not just top 5)
    delay_by_airline_df = (
        df.group_by("OPERA")
        .agg(pl.col("delay").mean().alias("rate"), pl.len().alias("count"))
        .sort("rate", descending=True)
    )

    # Ensure all 16 airlines are represented (fill missing with 0)
    airline_rates = {row["OPERA"]: row["rate"] for row in delay_by_airline_df.to_dicts()}
    airline_counts = {row["OPERA"]: row["count"] for row in delay_by_airline_df.to_dicts()}

    delay_by_airline = {
        "airlines": all_airlines,
        "rates": [airline_rates.get(a, 0.0) for a in all_airlines],
        "counts": [airline_counts.get(a, 0) for a in all_airlines]
    }

    # ALL 12 months
    all_months = list(range(1, 13))
    delay_by_month_df = (
        df.group_by("MES")
        .agg(pl.col("delay").mean().alias("rate"), pl.len().alias("count"))
        .sort("MES")
    )

    month_rates = {row["MES"]: row["rate"] for row in delay_by_month_df.to_dicts()}
    month_counts = {row["MES"]: row["count"] for row in delay_by_month_df.to_dicts()}

    delay_by_month = {
        "months": all_months,
        "rates": [month_rates.get(m, 0.0) for m in all_months],
        "counts": [month_counts.get(m, 0) for m in all_months]
    }

    # By TIPOVUELO (I and N)
    delay_by_tipovuelo_df = (
        df.group_by("TIPOVUELO")
        .agg(pl.col("delay").mean().alias("rate"), pl.len().alias("count"))
    )
    delay_by_tipovuelo = {
        tipovuelo: {"rate": row["rate"], "count": row["count"]}
        for row in delay_by_tipovuelo_df.to_dicts()
        for tipovuelo in [row["TIPOVUELO"]]
    }

    # Cross-analysis: airline x month (top combinations)
    airline_month_df = (
        df.group_by(["OPERA", "MES"])
        .agg(pl.col("delay").mean().alias("rate"), pl.len().alias("count"))
        .filter(pl.col("count") > 50)  # Only significant samples
        .sort("rate", descending=True)
        .head(10)
    )
    top_combinations = airline_month_df.to_dicts()

    # Worst months (top 3)
    month_sorted = sorted(
        [{"MES": m, "rate": month_rates.get(m, 0.0)} for m in all_months],
        key=lambda x: x["rate"],
        reverse=True
    )
    worst_months = month_sorted[:3]

    return {
        "total_flights": total_flights,
        "total_delays": total_delays,
        "delay_rate": round(delay_rate, 3),
        "delay_by_airline": delay_by_airline,
        "delay_by_month": delay_by_month,
        "delay_by_tipovuelo": delay_by_tipovuelo,
        "top_combinations": top_combinations,
        "worst_months": worst_months,
    }


def generate_and_save_context(
    csv_path: str = "data/data.csv",
    output_path: str = "data/context.json"
) -> None:
    """Genera contexto con Polars y lo guarda como JSON.

    Esta función DEBE ejecutarse durante el build del contenedor.
    NO debe ejecutarse en request time.
    """
    context = generate_context(csv_path)
    with open(output_path, "w") as f:
        json.dump(context, f, indent=2)


def load_context(json_path: str = "data/context.json") -> Dict[str, Any]:
    """Carga contexto precomputado desde JSON (request time)."""
    with open(json_path, "r") as f:
        return json.load(f)


# Contexto cacheado en memoria (una vez cargado, no vuelve a leer el archivo)
_context_cache: Optional[Dict[str, Any]] = None


def get_cached_context(json_path: str = "data/context.json") -> Dict[str, Any]:
    """Carga y cachea el contexto en memoria para requests múltiples."""
    global _context_cache
    if _context_cache is None:
        _context_cache = load_context(json_path)
    return _context_cache


def build_prompt(question: str, context: Dict[str, Any]) -> list[Dict[str, str]]:
```

**Response (200 OK):**
```json
{
  "insight": "Según el análisis de los datos históricos, LATAM en diciembre tiene una tasa de retraso del 22%, siendo diciembre el segundo mes con mayor retrasos del año. Los vuelos internacionales (TIPOVUELO_I) representan el 78% de los retrasos, especialmente hacia destinos en Brasil y Argentina. Esto se debe a la alta demanda de viajeros vacaciones y condiciones climáticas переменчив в la zona sur de Sudamérica.",
  "context_used": {
    "total_flights": 682,
    "delay_rate": 0.22,
    "top_airline": "LATAM",
    "month": 12,
    "month_delay_rate": 0.31
  }
}
```

**Error Response (500):**
```json
{
  "error": "LLM call failed: connection timeout"
}
```

---

### Polars: Contexto Automático

La función `generate_context(csv_path)` extrae automáticamente:

```python
{
    "total_flights": int,
    "delay_rate": float,  # % general de retrasos
    "total_delays": int,
    "delay_by_airline": {  # top 5
        "LATAM": 0.18,
        "Sky Airline": 0.21,
        ...
    },
    "delay_by_month": {  # todos los meses
        "1": 0.12,
        "7": 0.28,
        "12": 0.31,
        ...
    },
    "delay_by_tipovuelo": {"I": 0.19, "N": 0.14},
    "top_delay_reasons": ["weather", "airline_ops", "demand"],
    "data_sample": "últimas 5 filas representativas"
}
```

Este contexto se pasa al LLM como parte del prompt.

---

### LLM: System Prompt

```python
SYSTEM_PROMPT = """Eres un analista de datos experto en retrasos de vuelos del aeropuerto SCL (Santiago de Chile).

Tienes acceso a estadísticas históricas de vuelos y retrasos. Based on the provided context, responde preguntas sobre patrones de retrasos, comparaciones entre aerolineas, y análisis predictivo.

Rules:
1. Responde SIEMPRE en español
2. Usa números y estadísticas del contexto cuando estén disponibles
3. Si no tienes suficiente información, dilo claramente
4. Sé conciso pero informativo (máximo 3-4 oraciones para respuestas simples)
5. Para análisis complejos, estructura tu respuesta con bullet points

Contexto de los datos:
{context}

Pregunta del usuario: {question}
"""
```

---

### Implementación Paso a Paso

#### Paso 9.1: Crear `challenge/ai_insights.py`

```python
from __future__ import annotations

import os
from typing import Dict, Any

import httpx
import polars as pl


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "claude-sonnet-4"

SYSTEM_PROMPT = """Eres un analista de datos experto en retrasos de vuelos del aeropuerto SCL (Santiago de Chile).

DATASET:
- Fuente: data/data.csv (~682k vuelos históricos)
- Columnas principales:
  - OPERA: Nombre de aerolinea (16 válidas: American Airlines, Air France, Aerolineas Argentinas, Avianca, British Airways, Copa Air, Delta Air, Grupo LATAM, Iberia, JetSmart, Korean Air, LATAM, Latin American Wings, Lloyd Aereo Boliviano, Sky Airline, United Airlines)
  - TIPOVUELO: I=Internacional, N=Nacional
  - MES: Mes de operación (1-12)
  - Fecha-I: Fecha inicio (scheduled)
  - Fecha-O: Fecha operación (actual)
  - delay: Target binario (1 si Fecha-O - Fecha-I > 15 minutos, 0 si no)

TOP 10 FEATURES DEL MODELO XGBOOST:
- OPERA_Latin American Wings, MES_7, MES_10, OPERA_Grupo LATAM, MES_12, TIPOVUELO_I, MES_4, MES_11, OPERA_Sky Airline, OPERA_Copa Air

REGLAS:
1. Responde SIEMPRE en español
2. Usa números y estadísticas del contexto cuando estén disponibles
3. Si no tienes suficiente información, dilo claramente
4. Sé conciso pero informativo (máximo 3-4 oraciones para respuestas simples)
5. Para análisis complejos, usa bullet points
6. IMPORTANTE: Delay se define como >15 minutos de diferencia entre Fecha-O y Fecha-I
7. No especular sobre razones no respaldadas por los datos

Contexto de los datos:
{context}

Pregunta del usuario: {question}
"""


def generate_context(csv_path: str = "data/data.csv") -> Dict[str, Any]:
    """Extrae estadísticas relevantes del CSV usando Polars.

    Incluye stats para las 16 aerolineas, los 12 meses, y ambos tipos de vuelo.
    """
    df = pl.read_csv(csv_path, low_memory=False)

    total_flights = len(df)
    total_delays = df.filter(pl.col("delay") == 1).height
    delay_rate = total_delays / total_flights if total_flights > 0 else 0

    # ALL 16 airlines (sorted by name for consistency)
    all_airlines = [
        "American Airlines", "Air France", "Aerolineas Argentinas", "Avianca",
        "British Airways", "Copa Air", "Delta Air", "Grupo LATAM", "Iberia",
        "JetSmart", "Korean Air", "LATAM", "Latin American Wings",
        "Lloyd Aereo Boliviano", "Sky Airline", "United Airlines"
    ]

    # Delay by airline (ALL 16, not just top 5)
    delay_by_airline_df = (
        df.group_by("OPERA")
        .agg(pl.col("delay").mean().alias("rate"), pl.len().alias("count"))
        .sort("rate", descending=True)
    )

    # Ensure all 16 airlines are represented (fill missing with 0)
    airline_rates = {row["OPERA"]: row["rate"] for row in delay_by_airline_df.to_dicts()}
    airline_counts = {row["OPERA"]: row["count"] for row in delay_by_airline_df.to_dicts()}

    delay_by_airline = {
        "airlines": all_airlines,
        "rates": [airline_rates.get(a, 0.0) for a in all_airlines],
        "counts": [airline_counts.get(a, 0) for a in all_airlines]
    }

    # ALL 12 months
    all_months = list(range(1, 13))
    delay_by_month_df = (
        df.group_by("MES")
        .agg(pl.col("delay").mean().alias("rate"), pl.len().alias("count"))
        .sort("MES")
    )

    month_rates = {row["MES"]: row["rate"] for row in delay_by_month_df.to_dicts()}
    month_counts = {row["MES"]: row["count"] for row in delay_by_month_df.to_dicts()}

    delay_by_month = {
        "months": all_months,
        "rates": [month_rates.get(m, 0.0) for m in all_months],
        "counts": [month_counts.get(m, 0) for m in all_months]
    }

    # By TIPOVUELO (I and N)
    delay_by_tipovuelo_df = (
        df.group_by("TIPOVUELO")
        .agg(pl.col("delay").mean().alias("rate"), pl.len().alias("count"))
    )
    delay_by_tipovuelo = {
        tipovuelo: {"rate": row["rate"], "count": row["count"]}
        for row in delay_by_tipovuelo_df.to_dicts()
        for tipovuelo in [row["TIPOVUELO"]]
    }

    # Cross-analysis: airline x month (top combinations)
    airline_month_df = (
        df.group_by(["OPERA", "MES"])
        .agg(pl.col("delay").mean().alias("rate"), pl.len().alias("count"))
        .filter(pl.col("count") > 50)  # Only significant samples
        .sort("rate", descending=True)
        .head(10)
    )
    top_combinations = airline_month_df.to_dicts()

    # Worst months (top 3)
    month_sorted = sorted(
        [{"MES": m, "rate": month_rates.get(m, 0.0)} for m in all_months],
        key=lambda x: x["rate"],
        reverse=True
    )
    worst_months = month_sorted[:3]

    return {
        "total_flights": total_flights,
        "total_delays": total_delays,
        "delay_rate": round(delay_rate, 3),
        "delay_by_airline": delay_by_airline,
        "delay_by_month": delay_by_month,
        "delay_by_tipovuelo": delay_by_tipovuelo,
        "top_combinations": top_combinations,
        "worst_months": worst_months,
    }


def build_prompt(question: str, context: Dict[str, Any]) -> list[Dict[str, str]]:
    """Arma los mensajes para el LLM."""
    context_str = _format_context(context)
    system = SYSTEM_PROMPT.format(context=context_str, question=question)

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": question}
    ]


def _format_context(context: Dict[str, Any]) -> str:
    """Formatea el contexto para el prompt."""
    lines = [
        f"Total de vuelos analizados: {context['total_flights']:,}",
        f"Total de retrasos: {context['total_delays']:,} ({context['delay_rate']:.1%})",
        "",
        "=" * 50,
        "ESTADISTICAS POR AEROLINEA (las 16):",
        "=" * 50,
    ]

    airlines = context["delay_by_airline"]["airlines"]
    rates = context["delay_by_airline"]["rates"]
    counts = context["delay_by_airline"]["counts"]

    for airline, rate, count in zip(airlines, rates, counts):
        lines.append(f"  {airline:30s} | Delay: {rate:5.1%} | Vuelos: {count:6,}")

    lines.extend([
        "",
        "=" * 50,
        "ESTADISTICAS POR MES (1-12):",
        "=" * 50,
    ])

    months = context["delay_by_month"]["months"]
    month_rates = context["delay_by_month"]["rates"]
    month_counts = context["delay_by_month"]["counts"]

    month_names = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                  "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

    for mes, rate, count, nombre in zip(months, month_rates, month_counts, month_names):
        lines.append(f"  Mes {mes:2d} ({nombre}) | Delay: {rate:5.1%} | Vuelos: {count:6,}")

    lines.extend([
        "",
        "=" * 50,
        "ESTADISTICAS POR TIPO DE VUELO:",
        "=" * 50,
    ])

    tipovuelo = context["delay_by_tipovuelo"]
    i_data = tipovuelo.get("I", {"rate": 0, "count": 0})
    n_data = tipovuelo.get("N", {"rate": 0, "count": 0})
    lines.append(f"  Internacional (I) | Delay: {i_data['rate']:5.1%} | Vuelos: {i_data['count']:6,}")
    lines.append(f"  Nacional     (N) | Delay: {n_data['rate']:5.1%} | Vuelos: {n_data['count']:6,}")

    lines.extend([
        "",
        "=" * 50,
        "PEORES MESES PARA VOLAR (top 3):",
        "=" * 50,
    ])

    month_names_dict = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                       5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
                       9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}

    for item in context["worst_months"]:
        mes = item["MES"]
        rate = item["rate"]
        lines.append(f"  {month_names_dict.get(mes, mes)} (Mes {mes}): {rate:.1%} de retrasos")

    lines.extend([
        "",
        "=" * 50,
        "COMBINACIONES AEROLINEA + MES MAS PROBLEMÁTICAS (top 10):",
        "=" * 50,
    ])

    for i, combo in enumerate(context["top_combinations"], 1):
        opera = combo["OPERA"]
        mes = combo["MES"]
        rate = combo["rate"]
        count = combo["count"]
        lines.append(f"  {i:2d}. {opera:25s} + Mes {mes:2d} | Delay: {rate:5.1%} | Vuelos: {count:5,}")

    return "\n".join(lines)


async def call_llm(prompt: list[Dict[str, str]], model: str = DEFAULT_MODEL) -> str:
    """Llama al LLM via OpenRouter."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY environment variable not set")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": prompt,
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def get_ai_insight(question: str) -> Dict[str, Any]:
    """Función principal del endpoint.

    USA get_cached_context() para request time (no usa Polars).
    El contexto fue precomputado en build time y guardado en data/context.json.
    """
    context = get_cached_context()
    prompt = build_prompt(question, context)

    try:
        insight = await call_llm(prompt)
        return {
            "insight": insight,
            "context_used": {
                "total_flights": context["total_flights"],
                "delay_rate": context["delay_rate"]
            }
        }
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {str(e)}")
```

---

#### Paso 9.2: Modificar `challenge/api.py`

Agregar el endpoint `/ai-insights`:

```python
from challenge.ai_insights import get_ai_insight


class AIInsightRequest(BaseModel):
    question: str
    model: Optional[str] = None


@app.post(
    "/ai-insights",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid question"},
        500: {"description": "LLM call failed"}
    }
)
async def ai_insights(request: AIInsightRequest) -> Dict[str, Any]:
    """Get AI-powered insights about flight delays.

    Uses Polars to extract context from data.csv and MiniMax LLM
    to generate conversational analysis.

    Args:
        request: Contains the question to ask about the data.

    Returns:
        Dict with 'insight' key containing the LLM response.
    """
    try:
        result = await get_ai_insight(request.question)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
```

---

#### Paso 9.3: Crear `tests/ai/test_ai_insights.py`

```python
import json
import os
import pytest
from unittest.mock import patch, AsyncMock, mock_open

from challenge.ai_insights import (
    generate_context,
    generate_and_save_context,
    load_context,
    get_cached_context,
    build_prompt,
    _format_context,
    call_llm,
    get_ai_insight
)


class TestPolarsContext:
    """Tests for Polars context generation (build time)."""

    def test_generate_context_returns_dict(self):
        """Context is a dictionary with expected keys."""
        context = generate_context()
        assert isinstance(context, dict)
        assert "total_flights" in context
        assert "delay_rate" in context

    def test_generate_context_has_airlines(self):
        """Context includes delay by airline."""
        context = generate_context()
        assert "delay_by_airline" in context
        assert len(context["delay_by_airline"]["airlines"]) == 16

    def test_generate_context_has_months(self):
        """Context includes all 12 months."""
        context = generate_context()
        assert "delay_by_month" in context
        assert len(context["delay_by_month"]["months"]) == 12

    def test_delay_rate_is_percentage(self):
        """Delay rate is between 0 and 1."""
        context = generate_context()
        assert 0 <= context["delay_rate"] <= 1


class TestContextPersistence:
    """Tests for JSON save/load (build time)."""

    def test_generate_and_save_context_creates_file(self, tmp_path):
        """generate_and_save_context creates a JSON file."""
        csv_path = "data/data.csv"
        output_path = tmp_path / "context.json"

        generate_and_save_context(csv_path, str(output_path))

        assert output_path.exists()
        with open(output_path, "r") as f:
            data = json.load(f)
        assert "total_flights" in data
        assert "delay_rate" in data

    def test_load_context_returns_dict(self, tmp_path):
        """load_context returns dictionary from JSON."""
        context_data = {"total_flights": 1000, "delay_rate": 0.15}
        json_path = tmp_path / "context.json"

        with open(json_path, "w") as f:
            json.dump(context_data, f)

        loaded = load_context(str(json_path))
        assert loaded == context_data


class TestCachedContext:
    """Tests for cached context (request time)."""

    def test_get_cached_context_returns_dict(self):
        """get_cached_context returns the context dictionary."""
        with patch("challenge.ai_insights.load_context") as mock_load:
            mock_load.return_value = {"total_flights": 1000, "delay_rate": 0.15}

            # Reset cache for test isolation
            import challenge.ai_insights
            challenge.ai_insights._context_cache = None

            result = get_cached_context()
            assert result == {"total_flights": 1000, "delay_rate": 0.15}

    def test_get_cached_context_caches_result(self):
        """get_cached_context caches the result to avoid repeated reads."""
        with patch("challenge.ai_insights.load_context") as mock_load:
            mock_load.return_value = {"total_flights": 1000, "delay_rate": 0.15}

            # Reset cache
            import challenge.ai_insights
            challenge.ai_insights._context_cache = None

            # First call
            get_cached_context()
            # Second call
            get_cached_context()

            # load_context should be called only once
            assert mock_load.call_count == 1


class TestPromptBuilding:
    """Tests for prompt construction."""

    def test_build_prompt_returns_list(self):
        """Prompt is a list of message dicts."""
        context = {
            "total_flights": 100,
            "delay_rate": 0.15,
            "delay_by_airline": {"airlines": [], "rates": [], "counts": []},
            "delay_by_month": {"months": [], "rates": [], "counts": []},
            "delay_by_tipovuelo": {},
            "top_combinations": [],
            "worst_months": []
        }
        prompt = build_prompt("Why are flights delayed?", context)
        assert isinstance(prompt, list)
        assert len(prompt) >= 1

    def test_prompt_has_system_and_user(self):
        """Prompt contains system and user messages."""
        context = {
            "total_flights": 100,
            "delay_rate": 0.15,
            "delay_by_airline": {"airlines": [], "rates": [], "counts": []},
            "delay_by_month": {"months": [], "rates": [], "counts": []},
            "delay_by_tipovuelo": {},
            "top_combinations": [],
            "worst_months": []
        }
        prompt = build_prompt("Why are flights delayed?", context)
        roles = [m["role"] for m in prompt]
        assert "system" in roles
        assert "user" in roles


class TestFormatContext:
    """Tests for context formatting."""

    def test_format_context_includes_numbers(self):
        """Formatted context includes flight numbers."""
        context = {
            "total_flights": 682,
            "delay_rate": 0.15,
            "delay_by_airline": {"OPERA": ["LATAM"], "rate": [0.18]},
            "delay_by_month": {"MES": [12], "rate": [0.31]},
            "delay_by_tipovuelo": {"TIPOVUELO": ["I"], "rate": [0.19]}
        }
        formatted = _format_context(context)
        assert "682" in formatted
        assert "LATAM" in formatted


class TestLLMCall:
    """Tests for LLM integration."""

    @pytest.mark.asyncio
    @patch("challenge.ai_insights.httpx.AsyncClient")
    async def test_call_llm_success(self, mock_client):
        """Successful LLM call returns content."""
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_response.raise_for_status = lambda: None

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        prompt = [{"role": "user", "content": "test"}]
        result = await call_llm(prompt)
        assert result == "Test response"

    @pytest.mark.asyncio
    async def test_call_llm_no_api_key(self):
        """Error when OPENROUTER_API_KEY is not set."""
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": ""}):
            prompt = [{"role": "user", "content": "test"}]
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                await call_llm(prompt)


class TestGetInsight:
    """Tests for the main insight function."""

    @pytest.mark.asyncio
    @patch("challenge.ai_insights.call_llm", new_callable=AsyncMock)
    async def test_get_ai_insight_returns_dict(self, mock_llm):
        """Function returns dict with insight and context."""
        mock_llm.return_value = "Los vuelos en diciembre tienen más retrasos."

        result = await get_ai_insight("¿Por qué se retrasan los vuelos?")

        assert isinstance(result, dict)
        assert "insight" in result
        assert "context_used" in result

    @pytest.mark.asyncio
    @patch("challenge.ai_insights.call_llm", new_callable=AsyncMock)
    async def test_get_ai_insight_error_handling(self, mock_llm):
        """Function raises RuntimeError on LLM failure."""
        mock_llm.side_effect = Exception("Connection failed")

        with pytest.raises(RuntimeError, match="LLM call failed"):
            await get_ai_insight("¿Por qué se retrasan los vuelos?")
```

---

#### Paso 9.4: Agregar a requirements.txt

```txt
# requirements.txt (append)
polars>=1.0.0
httpx>=0.24.0
```

---

#### Paso 9.5: Agregar a Makefile

```makefile
.PHONY: ai-test
ai-test:       ## Run AI insights tests
    mkdir reports || true
    pytest tests/ai/test_ai_insights.py -v
```

---

#### Paso 9.6: Agregar al CI/CD

En `.github/workflows/ci.yml`, agregar después de api-test:

```yaml
      - name: Run AI insights tests
        run: python -m pytest tests/ai/test_ai_insights.py -v
```

---

#### Paso 9.7: Configurar OPENROUTER_API_KEY en GitHub

1. Ir a: https://github.com/aliagenttucuman-byte/latam-flight-delay/settings/secrets/actions
2. Click **"New repository secret"**
3. Nombre: `OPENROUTER_API_KEY`
4. Valor: (tu API key de OpenRouter)
5. Save

---

#### Paso 9.8: Actualizar Dockerfile

El Dockerfile necesita ejecutar `generate_and_save_context()` durante build para generar el archivo `data/context.json`.

```dockerfile
# syntax=docker/dockerfile:1.2
FROM python:3.11-slim

WORKDIR /app

COPY requirements*.txt ./

RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-test.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

COPY challenge/ ./challenge/
COPY data/ ./data/

# Generate context.json during build (only once)
RUN python -c "from challenge.ai_insights import generate_and_save_context; generate_and_save_context()"

ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

CMD ["uvicorn", "challenge.api:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Nota:** El archivo `data/context.json` se genera en build time y se incluye en el contenedor. En request time, `get_cached_context()` solo lee el JSON (~50KB, ~1ms), sin usar Polars.

---

### Tests para Ejecutar

```bash
# Local
make ai-test

# Via Docker
docker run delay-model-api:latest pytest tests/ai/test_ai_insights.py -v

# En GitHub Actions (automático en CI)
```

---

### Llamar al Endpoint

```bash
# Test local (si la API está corriendo en puerto 8080)
curl -X POST "http://localhost:8080/ai-insights" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es el mejor mes para volar sin retrasos?"}'

# Test en producción (GCP)
curl -X POST "https://delay-model-api-chxpmithta-rj.a.run.app/ai-insights" \
  -H "Content-Type: application/json" \
  -d '{"question": "¿Cuál es el mejor mes para volar sin retrasos?"}'
```

---

### Respuestas de Ejemplo

**Pregunta:** `¿Por qué se retrasan los vuelos en julio?`

**Respuesta:**
```
Julio es el mes con mayor tasa de retrasos (28%), seguido de diciembre (31%) y noviembre (27%). Esto se debe principalmente a:

• Condiciones climáticas invernales en la zona andina (最少 nevadas y tormentas)
• Alta demanda de vuelos hacia destinos turísticos de invierno (Brasil, Argentina)
• Sky Airline tiene la tasa de retrasos más alta (21%) en julio, mientras que LATAM opera el 45% de los vuelos ese mes
• Los vuelos internacionales (I) tienen 5% más retrasos que los nacionales (N) en este periodo

Recomendación: Si volás en julio, elegí清晨 first flights para evitar retrasos acumulados.
```

---

### Notas Importantes

1. **No afecta el deploy existente**: Agregar este endpoint no cambia el CD. Solo agrega un nuevo route.

2. **Polars no reemplaza a Pandas**: Solo se usa Polars para el endpoint AI. El modelo existente sigue usando Pandas/sklearn.

3. **Timeout del LLM**: 60 segundos. El endpoint puede tardar en responder dependiendo del LLM.

4. **Costo**: OpenRouter tiene tier gratuito para MiniMax 2.5. El costo debería ser $0 o muy bajo para la PoC.

5. **RAG simple**: El contexto se genera fresh en cada request (no hay vector store). Para una PoC está bien, pero en producción se podría cachear el contexto o usar embeddings.

---

### Checklist de Implementación

| Paso | Descripción | Estado |
|------|-------------|--------|
| 9.1 | Crear `challenge/ai_insights.py` | ⏳ pending |
| 9.2 | Modificar `challenge/api.py` (agregar endpoint) | ⏳ pending |
| 9.3 | Crear `tests/ai/test_ai_insights.py` | ⏳ pending |
| 9.4 | Agregar `polars` y `httpx` a `requirements.txt` | ⏳ pending |
| 9.5 | Agregar `make ai-test` al Makefile | ⏳ pending |
| 9.6 | Agregar AI tests al CI workflow | ⏳ pending |
| 9.7 | Configurar `OPENROUTER_API_KEY` en GitHub Secrets | ⏳ pending |
| 9.8 | Testear endpoint localmente | ⏳ pending |
| 9.9 | Push y verificar CI/CD | ⏳ pending |

---

### Notas sobre OpenRouter y MiniMax

**OpenRouter** es un aggregator que permite acceder a múltiples LLMs con una API unificada. MiniMax 2.5 es uno de los modelos disponibles en su catálogo.

**Endpoints disponibles:**
- Chat completions: `POST https://openrouter.ai/api/v1/chat/completions`
- Models list: `GET https://openrouter.ai/api/v1/models`

**Model ID para MiniMax:** `minimax/minimax-2.5`

**Rate limits (tier gratuito):**
- 50 requests/minuto
- 5000 requests/día

Para la PoC es más que suficiente.

---

## Resumen de Cambios

```
NEW FILES:
  challenge/ai_insights.py       (core logic)
  tests/ai/test_ai_insights.py   (unit tests)

MODIFIED FILES:
  challenge/api.py               (+ /ai-insights endpoint)
  requirements.txt               (+ polars, httpx)
  Makefile                       (+ ai-test target)
  .github/workflows/ci.yml       (+ AI tests in pipeline)

NEW SECRETS:
  OPENROUTER_API_KEY            (GitHub Secrets)

NEW ENDPOINT:
  POST /ai-insights             (AI-powered flight delay analysis)
```

---

**Nota:** Este feature es una PoC. No se espera que sea production-ready (sin caching, sin rate limiting en el LLM, sin retry logic robusto). El objetivo es demostrar el concepto de RAG con datos de vuelos y MiniMax.

---

## Flujo develop → main con CI/CD (Opción B)

### Concepto

```
push a develop → CI corre en develop → CD deploya a Cloud Run desde develop → si OK → auto-merge develop→main
```

### Cambios en `.github/workflows/cd.yml`

```yaml
name: 'Continuous Delivery'

on:
  push:
    branches: [develop]  # CAMBIO: main → develop

permissions:
  contents: write  # CAMBIO: necesario para poder hacer merge a main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Necesario para poder hacer merge
          token: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up GCP
        run: gcloud config set project ${{ secrets.GCP_PROJECT_ID }}

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy delay-model-api \
            --source . \
            --region ${{ secrets.GCP_REGION }} \
            --platform managed \
            --allow-unauthenticated \
            --memory 512M \
            --cpu 1 \
            --set-env-vars "OPENROUTER_API_KEY=${{ secrets.OPENROUTER_API_KEY }}"

      - name: Merge to main
        if: success()
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git checkout main
          git merge develop --no-ff -m "Merge develop into main after successful CD"
          git push origin main
```

### Pasos para implementar

#### Paso 1: Modificar `.github/workflows/cd.yml`

Cambiar:
- `branches: [main]` → `branches: [develop]`
- Agregar `permissions: contents: write`
- Agregar `fetch-depth: 0` en checkout (para poder hacer merge)
- Agregar step de merge después del deploy exitoso

#### Paso 2: Asegurarse que CI corre en develop

El `ci.yml` actual ya tiene:
```yaml
on:
  push:
    branches: [main, develop, 'feature/**']
  pull_request:
    branches: [main, develop]
```

No necesita cambios.

#### Paso 3: Probar el flujo

1. Hacer commit en `develop`:
   ```bash
   git checkout develop
   git add .
   git commit -m "tu cambio"
   git push origin develop
   ```

2. Verificar en GitHub Actions que:
   - CI workflow corre en el push a develop
   - CD workflow se dispara DESPUÉS de CI (porque el trigger es `push: [develop]`)
   - Si CI pasa, CD hace deploy y luego merge a main

3. Verificar que `main` se actualiza automáticamente

### Precauciones

1. **Branch Protection en main**: Si `main` está protegido, el merge automático fallará. Ir a GitHub > Settings > Branches > Add rule:
   - Pattern: `main`
   - ✅ Require pull request before merging (desmarcar si querés merge directo)
   - O agregar exception para `github-actions[bot]`

2. **GITHUB_TOKEN**: Por defecto, el token `secrets.GITHUB_TOKEN` tiene permisos de escritura en el repo. No necesita secret adicional.

3. **Conflictos**: Si hay conflictos entre `develop` y `main`, el merge automático fallará. Resolver conflictos manualmente antes de pushear.

### Verificación del flujo completo

```bash
# 1. Push a develop
git checkout develop
git commit --allow-empty -m "test: trigger CI/CD"
git push origin develop

# 2. Esperar ~5 min y verificar en GitHub Actions:
#    - ci.yml corre en develop ✓
#    - cd.yml corre en develop ✓
#    - cd.yml hace merge a main ✓

# 3. Verificar que main se actualizó
git fetch origin
git log origin/main --oneline -3
```

---

## FASE 10: UI React con Chatbot "SCL Insights"

### Resumen del Feature

Agregar una interfaz web React con chatbot conversacional integrado. El usuario puede:
- Hacer predicciones de retraso via formulario
- Consultar insights de datos via chatbot (SCL Insights)

### Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                             │
│                                                                      │
│  ┌──────────────────────┐    ┌──────────────────────┐             │
│  │     FlightForm        │    │   SCL Insights       │             │
│  │  ┌──────────────────┐ │    │   (Chatbot)          │             │
│  │  │ OPERA: [Dropdown]│ │    │                      │             │
│  │  │ TIPOVUELO:[Drop] │ │    │  Suggested questions  │             │
│  │  │ MES: [Dropdown]  │ │    │  + Chat history      │             │
│  │  │ [Predict]        │ │    │                      │             │
│  │  └──────────────────┘ │    │                      │             │
│  │  ┌──────────────────┐ │    │                      │             │
│  │  │ PredictionResult │ │    │                      │             │
│  │  │ (Shows result)   │ │    │                      │             │
│  │  └──────────────────┘ │    └──────────────────────┘             │
│  └──────────────────────┘                                          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐      ┌─────────────────────────┐
│   POST /predict         │      │   POST /ai-insights    │
│   (XGBoost prediction)  │      │   (LLM insights)        │
└─────────────────────────┘      └─────────────────────────┘
```

---

### Responsive Layout

| Dispositivo | Layout | Descripción |
|-------------|--------|-------------|
| **Mobile** (< 768px) | Stack vertical | Form arriba, Chatbot abajo |
| **Desktop** (>= 768px) | Grid 2 columnas | Form izquierda (40%), Chatbot derecha (60%) |

### Dark Mode

| Elemento | Color | Hex |
|----------|-------|-----|
| Background | Ultra dark | `#0f0f0f` |
| Cards/Surfaces | Dark gray | `#1a1a1a` |
| Border | Subtle | `#2a2a2a` |
| Text primary | White | `#ffffff` |
| Text secondary | Gray | `#a0a0a0` |
| LATAM accent | Red | `#CC0000` |
| Live indicator | Green | `#22c55e` |

### Componentes React

| Componente | Descripción | Props |
|------------|-------------|-------|
| `App.jsx` | Layout principal, dark mode, responsive grid | - |
| `Header.jsx` | Logo LATAM, título, live indicator | - |
| `FlightForm.jsx` | Formulario de predicción con validación | onPredict callback |
| `PredictionResult.jsx` | Muestra resultado de predicción | prediction, probabilidad |
| `SCLInsights.jsx` | Chatbot con sugerencias y chat history | - |

### Archivos Creados/Modificados

| Archivo | Cambio |
|---------|--------|
| `ui/` | NUEVO: Proyecto React Vite completo |
| `ui/src/App.jsx` | Componente principal con layout responsive |
| `ui/src/components/Header.jsx` | Header con logo y live indicator |
| `ui/src/components/FlightForm.jsx` | Formulario de predicción |
| `ui/src/components/PredictionResult.jsx` | Resultado de predicción |
| `ui/src/components/SCLInsights.jsx` | Chatbot conversacional |
| `ui/tailwind.config.js` | Config dark mode con `#0f0f0f` |
| `ui/src/index.css` | Estilos base con Tailwind |
| `static/` | NUEVO: Build output de React (copiado por Dockerfile) |
| `challenge/api.py` | MODIFICADO: Serve static files + FileResponse at root |
| `Dockerfile` | MODIFICADO: Copia `static/` al contenedor |

---

### Implementación Paso a Paso

#### Paso 10.1: Crear proyecto React con Vite

```bash
cd ui
npm create vite@latest . -- --template react
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

#### Paso 10.2: Configurar Tailwind con dark mode

```javascript
// tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        surface: '#1a1a1a',
        border: '#2a2a2a',
        latam: '#CC0000',
      }
    },
  },
  plugins: [],
}
```

```css
/* src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  background-color: #0f0f0f;
  color: #ffffff;
}
```

#### Paso 10.3: Crear componentes

```jsx
// src/components/Header.jsx
export function Header() {
  return (
    <header className="flex items-center gap-3 mb-6">
      <img src="/latam-logo.png" alt="LATAM" className="h-10" />
      <div>
        <h1 className="text-xl font-bold">SCL Flight Delay Predictor</h1>
        <div className="flex items-center gap-1.5 text-xs text-gray-400">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
          Live API
        </div>
      </div>
    </header>
  );
}
```

```jsx
// src/components/FlightForm.jsx
import { useState } from 'react';

const AIRLINES = ["American Airlines", "Air France", ...];
const TIPOS = ["I", "N"];
const MESES = [1, 2, ..., 12];

export function FlightForm({ onPredict }) {
  const [form, setForm] = useState({ OPERA: '', TIPOVUELO: '', MES: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ flights: [form] })
      });
      const data = await res.json();
      onPredict(data.predict[0]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <select value={form.OPERA} onChange={e => setForm({...form, OPERA: e.target.value})}>
        <option value="">Select Airline</option>
        {AIRLINES.map(a => <option key={a} value={a}>{a}</option>)}
      </select>
      <select value={form.TIPOVUELO} onChange={e => setForm({...form, TIPOVUELO: e.target.value})}>
        <option value="">Select Type</option>
        <option value="I">International</option>
        <option value="N">National</option>
      </select>
      <select value={form.MES} onChange={e => setForm({...form, MES: Number(e.target.value)})}>
        <option value="">Select Month</option>
        {MESES.map(m => <option key={m} value={m}>{m}</option>)}
      </select>
      <button type="submit" disabled={loading}>
        {loading ? 'Predicting...' : 'Predict Delay'}
      </button>
    </form>
  );
}
```

```jsx
// src/components/SCLInsights.jsx
const SUGGESTED_QUESTIONS = [
  "¿Por qué se retrasan los vuelos en diciembre?",
  "¿Cuál es la mejor aerolinea para volar?",
  "¿Qué mes tiene menos retrasos?"
];

export function SCLInsights() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendQuestion = async (question) => {
    setLoading(true);
    try {
      const res = await fetch('/ai-insights', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'user', content: question }, { role: 'assistant', content: data.insight }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <h2 className="text-lg font-semibold mb-4">SCL Insights</h2>
      <div className="flex flex-wrap gap-2 mb-4">
        {SUGGESTED_QUESTIONS.map(q => (
          <button key={q} onClick={() => sendQuestion(q)} className="text-sm px-3 py-1.5 rounded border border-[#2a2a2a] hover:border-[#CC0000]">
            {q}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-y-auto space-y-3">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            <span className={`inline-block px-3 py-2 rounded ${m.role === 'user' ? 'bg-[#CC0000]' : 'bg-[#1a1a1a]'}`}>
              {m.content}
            </span>
          </div>
        ))}
        {loading && <div className="text-gray-400">Consultando datos...</div>}
      </div>
      <form onSubmit={e => { e.preventDefault(); sendQuestion(input); setInput(''); }} className="mt-4 flex gap-2">
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Ask about flight delays..." className="flex-1 bg-[#1a1a1a] border border-[#2a2a2a] rounded px-3 py-2" />
        <button type="submit" disabled={loading}>Send</button>
      </form>
    </div>
  );
}
```

```jsx
// src/App.jsx
import { Header } from './components/Header';
import { FlightForm } from './components/FlightForm';
import { PredictionResult } from './components/PredictionResult';
import { SCLInsights } from './components/SCLInsights';
import { useState } from 'react';

export default function App() {
  const [prediction, setPrediction] = useState(null);

  return (
    <div className="min-h-screen bg-[#0f0f0f] text-white p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        <Header />
        <div className="grid grid-cols-1 md:grid-cols-[1fr_1.5fr] gap-6">
          <div className="space-y-6">
            <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#2a2a2a]">
              <FlightForm onPredict={setPrediction} />
              <PredictionResult prediction={prediction} />
            </div>
          </div>
          <div className="bg-[#1a1a1a] rounded-lg p-6 border border-[#2a2a2a]">
            <SCLInsights />
          </div>
        </div>
      </div>
    </div>
  );
}
```

#### Paso 10.4: Modificar api.py para servir UI

```python
# challenge/api.py - Agregar al final antes de app
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# Mount static files directory
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.get("/")
async def root():
    """Serve the React UI."""
    return FileResponse("static/index.html")
```

#### Paso 10.5: Actualizar Dockerfile

```dockerfile
# Dockerfile - Agregar después de COPY data/
COPY static/ ./static/
```

#### Paso 10.6: Build y copiar React a static/

```bash
cd ui
npm run build
# Copiar contenido de ui/dist/ a static/
```

---

### API Endpoints usados por la UI

| Endpoint | Método | Request | Response |
|----------|--------|---------|----------|
| `/predict` | POST | `{"flights": [{"OPERA": "...", "TIPOVUELO": "I", "MES": 7}]}` | `{"predict": [1]}` |
| `/ai-insights` | POST | `{"question": "¿Por qué se retrasan los vuelos?"}` | `{"insight": "...", "context_used": {...}}` |
| `/health` | GET | - | `{"status": "OK"}` |

---

### Checklist de Implementación

| Paso | Descripción | Estado |
|------|-------------|--------|
| 10.1 | Crear proyecto React con Vite | ✅ done |
| 10.2 | Configurar Tailwind CSS con dark mode | ✅ done |
| 10.3 | Crear componentes (Header, FlightForm, PredictionResult, SCLInsights) | ✅ done |
| 10.4 | Modificar api.py para servir static files | ✅ done |
| 10.5 | Actualizar Dockerfile para copiar static/ | ✅ done |
| 10.6 | Responsive layout (mobile stack, desktop grid) | ✅ done |
| 10.7 | LATAM branding (red #CC0000, logo) | ✅ done |
| 10.8 | Testear localmente en puerto 8001 | ✅ done |
| 10.9 | Agregar CORS middleware | ✅ done |
| 10.10 | Usar URLs relativas en UI (no localhost) | ✅ done |
| 10.11 | Remover .env con localhost para producción | ✅ done |

---

### Errores Encontrados y Soluciones

#### Error 1: CORS - No 'Access-Control-Allow-Origin' header

**Síntoma:** Browser bloquea requests desde `https://delay-model-api-xxx.a.run.app` a `localhost:8001`.

**Causa:** La UI tenía hardcodeado `http://localhost:8001` en `ui/.env` (VITE_API_URL).

**Fix:**
1. Eliminar `ui/.env` del repo
2. Cambiar default en `App.jsx`: `const API_URL = import.meta.env.VITE_API_URL || ''`
3. Rebuild UI: `cd ui && npm run build && cp -r dist/* ../static/`
4. Agregar CORS middleware en `api.py`:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Error 2: StaticFiles montado en /static en vez de /

**Síntoma:** Pantalla blanca, assets 404 (`/assets/...` no encontrado).

**Causa:** `app.mount("/static", StaticFiles(...))` servía assets en `/static/assets/` pero el HTML buscaba `/assets/`.

**Fix:** Montar en `/` con `html=True`:
```python
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
```

#### Error 3: CI tests fallan por static/ no existe

**Síntoma:** `RuntimeError: Directory 'static' does not exist` al correr tests desde `tests/model/`.

**Causa:** `StaticFiles` se inicializa al importar `api.py`, pero `tests/model/` no tiene `static/`.

**Fix:** Mount condicional:
```python
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
```

---

### Notas Importantes

1. **Puerto 8001 para local testing**: Docker corre en puerto 8001 porque 8000 está ocupado
2. **OPENROUTER_API_KEY**: Requerido para el chatbot `/ai-insights`. En local se pasa como env var, en GCP via GitHub Secrets
3. **Logo file**: El logo debe estar en `ui/src/assets/latam-logo.png` y copiado a `static/` durante build
4. **Chatbot suggestions**: Se muestran SIEMPRE, no desaparecen después del primer mensaje
5. **NO commitear `ui/.env`**: Usar `.gitignore` para excluirlo. En producción usar URLs relativas (empty string)

---

### Historial de Cambios (Actualizado)

| Fecha | Versión | Cambio |
|-------|---------|--------|
| 2026-05-07 | 2.0.0 | Agregada FASE 10: UI React con chatbot SCL Insights |
| 2026-05-07 | 2.0.1 | Fixes CORS, StaticFiles mount, URLs relativas, .env cleanup |

---

## Resumen de Feature Flags

| Feature | Status | Notes |
|---------|--------|-------|
| XGBoost model | ✅ Complete | Top 10 features, class balancing |
| FastAPI endpoint | ✅ Complete | `/predict`, `/health` |
| AI Insights (RAG) | ✅ Complete | `/ai-insights` con Polars + MiniMax |
| React UI | ✅ Complete | Dark mode, responsive, chatbot |
| CI/CD Pipeline | ✅ Complete | develop → main auto-merge |
| Local Docker | ✅ Complete | Puerto 8001, env var OPENROUTER_API_KEY |