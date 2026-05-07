from __future__ import annotations

# Changes from original:
#   - Using @validator instead of @field_validator (Pydantic 1.10.2 compatibility, not v2)
#   - See: Plan_Ejecucion.md section "Cambios Realizados vs Original"
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Annotated, List, Dict, Any, Optional

import pandas as pd
import numpy as np


from challenge.ai_insights import get_ai_insight


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc.errors())}
    )


_model: Any = None


def load_model() -> Any:
    """Load and fit the DelayModel on startup (lazy initialization)."""
    global _model

    if _model is not None:
        return _model

    from challenge.model import DelayModel

    model = DelayModel()

    data = pd.read_csv("data/data.csv", low_memory=False)

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

    except (ValueError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid data: {str(e)}"
        )
    except Exception as e:
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
        500: {"description": "LLM call failed"}
    }
)
async def ai_insights(request: AIInsightRequest) -> Dict[str, Any]:
    """Get AI-powered insights about flight delays.

    Uses Polars to extract context from data.csv (precomputed at build time)
    and MiniMax LLM to generate conversational analysis.

    Args:
        request: Contains the question to ask about the data.

    Returns:
        Dict with 'insight' key containing the LLM response.

    Raises:
        HTTPException 500: If LLM call fails.
    """
    try:
        result = await get_ai_insight(request.question)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


import os

static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")