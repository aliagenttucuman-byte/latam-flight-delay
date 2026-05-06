from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional

import httpx
import polars as pl


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://opencode.ai/zen/v1/chat/completions"
DEFAULT_MODEL = "minimax"

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
    columns_needed = ["OPERA", "TIPOVUELO", "MES", "Fecha-I", "Fecha-O"]
    df = pl.read_csv(csv_path, low_memory=False, columns=columns_needed)

    from datetime import datetime

    def parse_min_diff(row):
        try:
            fecha_o = datetime.strptime(row["Fecha-O"], "%Y-%m-%d %H:%M:%S")
            fecha_i = datetime.strptime(row["Fecha-I"], "%Y-%m-%d %H:%M:%S")
            return (fecha_o - fecha_i).total_seconds() / 60
        except:
            return None

    df = df.with_columns([
        pl.struct(["Fecha-I", "Fecha-O"]).map_elements(
            lambda s: parse_min_diff(s),
            return_dtype=pl.Float64
        ).alias("min_diff")
    ])
    df = df.with_columns([
        (pl.col("min_diff") > 15).cast(pl.Int8).alias("delay")
    ])

    total_flights = len(df)
    total_delays = df.filter(pl.col("delay") == 1).height
    delay_rate = total_delays / total_flights if total_flights > 0 else 0

    all_airlines = [
        "American Airlines", "Air France", "Aerolineas Argentinas", "Avianca",
        "British Airways", "Copa Air", "Delta Air", "Grupo LATAM", "Iberia",
        "JetSmart", "Korean Air", "LATAM", "Latin American Wings",
        "Lloyd Aereo Boliviano", "Sky Airline", "United Airlines"
    ]

    delay_by_airline_df = (
        df.group_by("OPERA")
        .agg(pl.col("delay").mean().alias("rate"), pl.len().alias("count"))
        .sort("rate", descending=True)
    )

    airline_rates = {row["OPERA"]: row["rate"] for row in delay_by_airline_df.to_dicts()}
    airline_counts = {row["OPERA"]: row["count"] for row in delay_by_airline_df.to_dicts()}

    delay_by_airline = {
        "airlines": all_airlines,
        "rates": [airline_rates.get(a, 0.0) for a in all_airlines],
        "counts": [airline_counts.get(a, 0) for a in all_airlines]
    }

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

    delay_by_tipovuelo_df = (
        df.group_by("TIPOVUELO")
        .agg(pl.col("delay").mean().alias("rate"), pl.len().alias("count"))
    )
    delay_by_tipovuelo = {
        tipovuelo: {"rate": row["rate"], "count": row["count"]}
        for row in delay_by_tipovuelo_df.to_dicts()
        for tipovuelo in [row["TIPOVUELO"]]
    }

    airline_month_df = (
        df.group_by(["OPERA", "MES"])
        .agg(pl.col("delay").mean().alias("rate"), pl.len().alias("count"))
        .filter(pl.col("count") > 50)
        .sort("rate", descending=True)
        .head(10)
    )
    top_combinations = airline_month_df.to_dicts()

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
    """Carga contexto precomputado desde JSON.

    Esta función es para request time. No usa Polars, solo lee el JSON.

    Args:
        json_path: Path al archivo JSON precomputado.

    Returns:
        Dict con el contexto cargado.
    """
    with open(json_path, "r") as f:
        return json.load(f)


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
                "HTTP-Referer": "https://github.com/aliagenttucuman-byte/latam-flight-delay",
                "X-Title": "Flight Delay Prediction API"
            },
            json={
                "model": model,
                "messages": prompt,
            }
        )
        if not response.is_success:
            raise RuntimeError(f"LLM API error: {response.status_code} - {response.text}")
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