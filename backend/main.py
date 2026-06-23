from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    # Uso recomendado: uvicorn backend.main:app --reload
    from .schemas import FilterRequest
    from .services import (
        calculate_kpis,
        get_aeropuertos_criticos,
        get_cancelaciones_por_aerolinea,
        get_distribucion_vuelos,
        get_filter_options,
        get_retraso_mensual,
        get_retraso_por_aerolinea,
        get_rutas_criticas,
        get_tabla_vuelos,
    )
except ImportError:
    # Respaldo para ejecutar: python backend/main.py
    from schemas import FilterRequest
    from services import (
        calculate_kpis,
        get_aeropuertos_criticos,
        get_cancelaciones_por_aerolinea,
        get_distribucion_vuelos,
        get_filter_options,
        get_retraso_mensual,
        get_retraso_por_aerolinea,
        get_rutas_criticas,
        get_tabla_vuelos,
    )


app = FastAPI(
    title="Flight Delay Analytics API",
    version="1.0.0",
    description="API para dashboard de análisis de vuelos, retrasos, OTP, cancelaciones y rutas críticas.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def payload(filters: FilterRequest | None) -> dict:
    if filters is None:
        return {}
    return filters.model_dump(exclude_none=True)


@app.get("/")
async def root():
    return {
        "message": "Flight Delay Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/filters")
async def filters_get():
    """Catálogo inicial de filtros."""
    return get_filter_options({})


@app.post("/api/filters")
async def filters_post(filters: FilterRequest):
    """Opciones dependientes según los filtros activos."""
    return get_filter_options(payload(filters))


@app.post("/api/kpis")
async def kpis(filters: FilterRequest):
    """KPIs principales del resumen ejecutivo."""
    return calculate_kpis(payload(filters))


@app.post("/api/retraso-aerolinea")
async def retraso_aerolinea(filters: FilterRequest):
    """Retraso promedio de llegada por aerolínea."""
    return get_retraso_por_aerolinea(payload(filters))


@app.post("/api/aeropuertos-criticos")
async def aeropuertos_criticos(filters: FilterRequest):
    """Aeropuertos de origen con mayor retraso acumulado."""
    return get_aeropuertos_criticos(payload(filters))


@app.post("/api/cancelaciones-aerolinea")
async def cancelaciones_aerolinea(filters: FilterRequest):
    """Porcentaje de cancelaciones por aerolínea."""
    return get_cancelaciones_por_aerolinea(payload(filters))


@app.post("/api/retraso-mensual")
async def retraso_mensual(filters: FilterRequest):
    """Evolución mensual de retrasos promedio."""
    return get_retraso_mensual(payload(filters))


@app.post("/api/rutas-criticas")
async def rutas_criticas(filters: FilterRequest):
    """Rutas origen-destino con mayor retraso acumulado."""
    return get_rutas_criticas(payload(filters))


@app.post("/api/distribucion-vuelos")
async def distribucion_vuelos(filters: FilterRequest):
    """Distribución de vuelos puntuales, retrasados, cancelados y desviados."""
    return get_distribucion_vuelos(payload(filters))


@app.post("/api/tabla-vuelos")
async def tabla_vuelos(filters: FilterRequest):
    """Tabla compacta de vuelos filtrados."""
    return get_tabla_vuelos(payload(filters))


# Aliases cortos por comodidad del frontend.
@app.post("/api/airline-delay")
async def airline_delay(filters: FilterRequest):
    return get_retraso_por_aerolinea(payload(filters))


@app.post("/api/critical-airports")
async def critical_airports(filters: FilterRequest):
    return get_aeropuertos_criticos(payload(filters))


@app.post("/api/cancellations")
async def cancellations(filters: FilterRequest):
    return get_cancelaciones_por_aerolinea(payload(filters))


import os, httpx
from pydantic import BaseModel

COLAB_URL = os.getenv("COLAB_NGROK_URL", "https://tightness-backslid-proud.ngrok-free.dev")

from typing import Optional

class PredictRequest(BaseModel):
    Distance: float
    DayOfWeek: int
    Month: int
    Year: int
    Airline: str
    Origin: str
    Dest: str
    DepTimeBlk: str
    CRSDepTime: int
    CRSArrTime: int
    DepHour: int
    # Opcionales — Colab los completa con defaults si no se envían
    ArrHour: Optional[int] = 11
    ArrTimeBlk: Optional[str] = "1100-1159"

@app.post("/api/predict")
async def predict(req: PredictRequest):
    """Envía el caso al Colab con Spark y devuelve la predicción."""
    url = COLAB_URL.rstrip("/") + "/predict"
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(url, json=req.model_dump())
        resp.raise_for_status()
        return resp.json()

@app.post("/api/predict/ngrok-url")
async def update_ngrok_url(body: dict):
    """Actualiza la URL de ngrok en runtime sin reiniciar el servidor."""
    global COLAB_URL
    COLAB_URL = body.get("url", COLAB_URL).rstrip("/")
    return {"url": COLAB_URL}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)