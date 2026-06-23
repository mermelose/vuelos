from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class FilterRequest(BaseModel):
    """Filtros enviados por el frontend.

    Se permiten campos extra para mantener compatibilidad con aliases del HTML
    y con futuras extensiones del datamart.
    """

    model_config = ConfigDict(extra="allow")

    # Tiempo
    anio: Optional[int] = None
    year: Optional[int] = None
    mes: Optional[int] = None
    month: Optional[int] = None
    mes_inicio: Optional[int] = None
    mes_fin: Optional[int] = None

    # Dimensiones principales del dashboard Streamlit original
    aerolinea: Optional[Any] = None
    airline: Optional[Any] = None
    dim_aerolinea_id: Optional[Any] = None

    origen: Optional[Any] = None
    origin: Optional[Any] = None
    dim_origen_id: Optional[Any] = None

    destino: Optional[Any] = None
    dest: Optional[Any] = None
    dim_destino_id: Optional[Any] = None

    # Dimensiones extendidas del datamart
    ruta: Optional[Any] = None
    route: Optional[Any] = None
    dim_ruta_id: Optional[Any] = None

    hora: Optional[Any] = None
    hour: Optional[Any] = None
    time_block: Optional[Any] = None
    dim_hora_id: Optional[Any] = None

    avion: Optional[Any] = None
    tail_number: Optional[Any] = None
    dim_avion_id: Optional[Any] = None

    vuelo: Optional[Any] = None
    flight: Optional[Any] = None
    flight_number: Optional[Any] = None
    dim_vuelo_id: Optional[Any] = None

    # Flags operacionales
    cancelado: Optional[Any] = None
    cancelled: Optional[Any] = None
    desviado: Optional[Any] = None
    diverted: Optional[Any] = None
    delayed15: Optional[Any] = None
    dep15: Optional[Any] = None


class KPIResponse(BaseModel):
    """KPIs principales del resumen ejecutivo."""

    total_vuelos: int
    retraso_salida_promedio: float
    retraso_llegada_promedio: float
    otp: float
    cancelaciones_pct: float
    vuelos_afectados_pct: float
    retraso_salida_acumulado_horas: float
    retraso_llegada_acumulado_horas: float


class ChartDataResponse(BaseModel):
    """Formato flexible para gráficos Chart.js / frontend."""

    labels: list[str]
    data: Optional[list[float]] = None
    datasets: Optional[list[dict[str, Any]]] = None
    rows: Optional[list[dict[str, Any]]] = None


class TableResponse(BaseModel):
    """Respuesta estándar para tablas."""

    rows: list[dict[str, Any]]


class FilterOptions(BaseModel):
    """Opciones disponibles para los selects del frontend."""

    years: list[list[Any]] = []
    months: list[list[Any]] = []
    airlines: list[list[Any]] = []
    origins: list[list[Any]] = []
    destinations: list[list[Any]] = []
    routes: list[list[Any]] = []
    hours: list[list[Any]] = []


class AsistenteVuelosRequest(BaseModel):
    """Payload del asistente conversacional."""

    pregunta: str
    filtros: dict[str, Any] = {}


class AssistantResponse(BaseModel):
    """Respuesta del asistente conversacional."""

    intent: dict[str, Any] = {}
    respuesta: str
    data: dict[str, Any] = {}
    fuentes: list[dict[str, Any]] = []
