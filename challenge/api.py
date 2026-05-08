from __future__ import annotations

# Uses @field_validator (Pydantic v2 syntax)
#   - Original skeleton used Pydantic 1.10.2 @validator
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Annotated, List, Dict, Any, Optional

import pandas as pd
import numpy as np
import logging
import time
import os

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from challenge.ai_insights import get_ai_insight

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Rate limiter: key by remote address
limiter = Limiter(key_func=get_remote_address)


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
    version="1.1.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.warning(f"Validation error: {exc.errors()} | Path: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc.errors())}
    )


_model: Any = None
_model_loading: bool = False


def load_model() -> Any:
    """Load the DelayModel from serialized file (fast) or train if needed."""
    global _model, _model_loading

    if _model is not None:
        return _model

    _model_loading = True
    logger.info("Loading model...")
    start = time.time()

    from challenge.model import DelayModel

    model = DelayModel()
    model_path = "data/delay_model.pkl"

    import os
    if os.path.isfile(model_path):
        logger.info(f"Loading pre-trained model from {model_path}")
        model.load(model_path)
        _model = model
        _model_loading = False
        elapsed = time.time() - start
        logger.info(f"Model loaded from disk in {elapsed:.2f}s")
        return _model

    logger.info("No serialized model found. Training from scratch...")
    data = pd.read_csv("data/data.csv", low_memory=False)
    features, target = model.preprocess(data, target_column="delay")
    model.fit(features, target)

    _model = model
    _model_loading = False
    elapsed = time.time() - start
    logger.info(f"Model trained in {elapsed:.2f}s")
    return _model


@app.get("/health")
@limiter.limit("60/minute")
async def get_health(request: Request) -> Dict[str, Any]:
    """Health check endpoint."""
    logger.info(f"Health check | Client: {request.client.host if request.client else 'unknown'}")
    if _model_loading:
        return {
            "status": "loading",
            "model_loaded": False,
            "version": "1.1.0"
        }
    return {
        "status": "OK",
        "model_loaded": _model is not None,
        "version": "1.1.0"
    }


@app.post(
    "/predict",
    response_model=Dict[str, List[int]],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Validation error - invalid flight data"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error during prediction"}
    }
)
@limiter.limit("30/minute")
async def predict(request: Request, batch: FlightBatch) -> Dict[str, List[int]]:
    """Predict flight delays for a batch of flights.

    Args:
        batch: Batch of flights containing OPERA, TIPOVUELO, MES.

    Returns:
        Dict with 'predict' key containing list of predictions (0 or 1).

    Raises:
        HTTPException 400: If any flight data fails validation.
        HTTPException 429: If rate limit exceeded.
        HTTPException 500: If prediction fails.
    """
    client = request.client.host if request.client else "unknown"
    logger.info(f"Predict request | Flights: {len(batch.flights)} | Client: {client}")
    start = time.time()

    try:
        model = load_model()

        flight_dicts = [
            {"OPERA": flight.OPERA, "TIPOVUELO": flight.TIPOVUELO, "MES": flight.MES}
            for flight in batch.flights
        ]
        flights_df = pd.DataFrame(flight_dicts)

        features = model.preprocess(flights_df)

        predictions = model.predict(features)

        elapsed = time.time() - start
        logger.info(f"Predict completed | Flights: {len(batch.flights)} | Time: {elapsed:.3f}s | Client: {client}")

        return {"predict": predictions}

    except (ValueError, ValidationError) as e:
        logger.warning(f"Predict validation error | Client: {client} | Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Predict error | Client: {client} | Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )


class AIInsightRequest(BaseModel):
    """Request model for AI insights endpoint."""

    question: Annotated[
        str,
        Field(
            description="Question about flight delays. Example questions:",
            examples=[
                "¿Por qué se retrasan los vuelos?",
                "¿Cuál es la aerolinea con más retrasos?",
                "¿Cuál es el peor mes para volar?",
                "¿Los vuelos internacionales tienen más retrasos que los nacionales?",
                "¿Qué combinación de aerolinea y mes es más problemática?",
                "¿Cuántos vuelos se analizaron?",
                "¿Cuál es la tasa de retrasos general?",
                "¿Cuál es el mejor mes para volar?"
            ]
        )
    ]


@app.post(
    "/ai-insights",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    responses={
        400: {"description": "Invalid question"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "LLM call failed"}
    }
)
@limiter.limit("10/minute")
async def ai_insights(request: Request, body: AIInsightRequest) -> Dict[str, Any]:
    """Get AI-powered insights about flight delays.

    Uses Polars to extract context from data.csv (precomputed at build time)
    and MiniMax LLM to generate conversational analysis.

    Args:
        body: Contains the question to ask about the data.

    Returns:
        Dict with 'insight' key containing the LLM response.

    Raises:
        HTTPException 429: If rate limit exceeded.
        HTTPException 500: If LLM call fails.
    """
    client = request.client.host if request.client else "unknown"
    logger.info(f"AI insights request | Question: {body.question[:50]}... | Client: {client}")
    start = time.time()

    try:
        result = await get_ai_insight(body.question)
        elapsed = time.time() - start
        logger.info(f"AI insights completed | Time: {elapsed:.2f}s | Client: {client}")
        return result
    except Exception as e:
        logger.error(f"AI insights error | Client: {client} | Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


static_dir = os.path.join(os.path.dirname(__file__), "..", "static")

@app.on_event("startup")
async def startup_event():
    """Log startup info and preload model in background."""
    logger.info("API starting up | Version: 1.1.0")
    import asyncio
    asyncio.create_task(asyncio.to_thread(load_model))

@app.get("/")
@limiter.limit("60/minute")
async def root(request: Request):
    """Serve the React UI."""
    index_path = os.path.join(static_dir, "index.html") if os.path.isdir(static_dir) else None
    if index_path and os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"message": "Flight Delay API - UI not built"}

if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")