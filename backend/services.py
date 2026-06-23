from __future__ import annotations

from typing import Any

import pandas as pd

from .database import (
    DIM_AEROLINEA,
    DIM_DESTINO,
    DIM_HORA,
    DIM_ORIGEN,
    DIM_RUTA,
    dim_options,
    get_filtered_fact,
    get_month_options,
    get_year_options,
)
from .schemas import ChartDataResponse, KPIResponse, TableResponse


# ============================================================
# Helpers
# ============================================================

def _round(value: Any, decimals: int = 2) -> float:
    try:
        if pd.isna(value):
            return 0.0
        return round(float(value), decimals)
    except Exception:
        return 0.0


def _numeric(df: pd.DataFrame, col: str, default: float = 0) -> pd.Series:
    if col not in df.columns:
        return pd.Series([default] * len(df), index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce")


def _first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _label_series(df: pd.DataFrame, candidates: list[str], fallback: str = "Sin dato") -> pd.Series:
    col = _first_existing(df, candidates)
    if col is None:
        return pd.Series([fallback] * len(df), index=df.index)
    return df[col].fillna(fallback).astype(str)


def _month_label(month: Any) -> str:
    month_names = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Setiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }
    try:
        return month_names.get(int(month), str(month))
    except Exception:
        return str(month)


def _empty_chart() -> ChartDataResponse:
    return ChartDataResponse(labels=[], data=[], rows=[])


def _top_n_from_filters(filters: dict | None, default: int = 15, max_n: int = 50) -> int:
    filters = filters or {}
    raw = filters.get("limit") or filters.get("top") or default
    try:
        return min(max(int(raw), 1), max_n)
    except Exception:
        return default


# ============================================================
# Opciones de filtros
# ============================================================

def get_filter_options(filters: dict | None = None) -> dict:
    """Devuelve opciones dependientes según los filtros activos.

    Si el usuario filtra por año, por ejemplo, las aerolíneas/orígenes/destinos
    se limitan a lo realmente presente en la fact table filtrada.
    """
    df = get_filtered_fact(filters, copy=False)

    airline_ids = df["dim_aerolinea_id"].dropna().unique().tolist() if "dim_aerolinea_id" in df.columns else None
    origin_ids = df["dim_origen_id"].dropna().unique().tolist() if "dim_origen_id" in df.columns else None
    dest_ids = df["dim_destino_id"].dropna().unique().tolist() if "dim_destino_id" in df.columns else None
    route_ids = df["dim_ruta_id"].dropna().unique().tolist() if "dim_ruta_id" in df.columns else None
    hour_ids = df["dim_hora_id"].dropna().unique().tolist() if "dim_hora_id" in df.columns else None

    return {
        "years": get_year_options(),
        "months": get_month_options(),
        "airlines": dim_options(DIM_AEROLINEA, "dim_aerolinea_id", ["Airline", "Operating_Airline"], airline_ids),
        "origins": dim_options(DIM_ORIGEN, "dim_origen_id", ["Origin", "OriginCityName", "OriginStateName"], origin_ids),
        "destinations": dim_options(DIM_DESTINO, "dim_destino_id", ["Dest", "DestCityName", "DestStateName"], dest_ids),
        "routes": dim_options(DIM_RUTA, "dim_ruta_id", ["Origin", "Dest", "DistanceGroup"], route_ids),
        "hours": dim_options(DIM_HORA, "dim_hora_id", ["TimeBlock", "Hora", "hhmm"], hour_ids),
    }


# ============================================================
# KPIs principales
# ============================================================

def calculate_kpis(filters: dict | None = None) -> KPIResponse:
    """Calcula los KPIs del resumen ejecutivo del dashboard."""
    df = get_filtered_fact(filters, copy=False)
    total = int(len(df))

    if total == 0:
        return KPIResponse(
            total_vuelos=0,
            retraso_salida_promedio=0,
            retraso_llegada_promedio=0,
            otp=0,
            cancelaciones_pct=0,
            vuelos_afectados_pct=0,
            retraso_salida_acumulado_horas=0,
            retraso_llegada_acumulado_horas=0,
        )

    dep_delay = _numeric(df, "DepDelayMinutes")
    arr_delay = _numeric(df, "ArrDelayMinutes")
    cancelled = _numeric(df, "Cancelled").fillna(0)
    diverted = _numeric(df, "Diverted").fillna(0)

    # Replicamos la lógica del Streamlit original:
    # OTP = porcentaje de vuelos con retraso de llegada <= 15 min.
    otp = (arr_delay <= 15).mean() * 100
    cancelaciones_pct = cancelled.mean() * 100

    affected = (arr_delay > 15) | (cancelled == 1) | (diverted == 1)
    vuelos_afectados_pct = affected.mean() * 100

    return KPIResponse(
        total_vuelos=total,
        retraso_salida_promedio=_round(dep_delay.mean(), 2),
        retraso_llegada_promedio=_round(arr_delay.mean(), 2),
        otp=_round(otp, 2),
        cancelaciones_pct=_round(cancelaciones_pct, 2),
        vuelos_afectados_pct=_round(vuelos_afectados_pct, 2),
        retraso_salida_acumulado_horas=_round(dep_delay.fillna(0).sum() / 60, 2),
        retraso_llegada_acumulado_horas=_round(arr_delay.fillna(0).sum() / 60, 2),
    )


# ============================================================
# Gráficos del dashboard
# ============================================================

def get_retraso_por_aerolinea(filters: dict | None = None) -> ChartDataResponse:
    """Retraso promedio de llegada por aerolínea."""
    df = get_filtered_fact(filters, copy=False)
    if df.empty:
        return _empty_chart()

    slim = pd.DataFrame({
        "_airline":   _label_series(df, ["Airline", "Operating_Airline", "Marketing_Airline"], "Sin aerolínea"),
        "_arr_delay": _numeric(df, "ArrDelayMinutes"),
    })

    result = (
        slim.groupby("_airline", as_index=False)["_arr_delay"]
        .mean()
        .rename(columns={"_airline": "aerolinea", "_arr_delay": "retraso_llegada_promedio"})
        .sort_values("retraso_llegada_promedio", ascending=False)
    )

    return ChartDataResponse(
        labels=result["aerolinea"].tolist(),
        data=result["retraso_llegada_promedio"].round(2).astype(float).tolist(),
        rows=result.round(2).to_dict(orient="records"),
    )


def get_aeropuertos_criticos(filters: dict | None = None) -> ChartDataResponse:
    """Aeropuertos de origen con mayor retraso acumulado de salida."""
    df = get_filtered_fact(filters, copy=False)
    if df.empty:
        return _empty_chart()

    top_n = _top_n_from_filters(filters, default=15)
    slim = pd.DataFrame({
        "_origin":      _label_series(df, ["Origin"], "Sin origen"),
        "_origin_city": _label_series(df, ["OriginCityName"], ""),
        "_dep_delay":   _numeric(df, "DepDelayMinutes").fillna(0),
    })
    df = slim

    result = (
        df.groupby(["_origin", "_origin_city"], as_index=False)["_dep_delay"]
        .sum()
        .rename(columns={"_origin": "origen", "_origin_city": "ciudad_origen", "_dep_delay": "retraso_salida_minutos"})
        .sort_values("retraso_salida_minutos", ascending=False)
        .head(top_n)
    )
    result["retraso_salida_horas"] = result["retraso_salida_minutos"] / 60

    return ChartDataResponse(
        labels=result["origen"].tolist(),
        data=result["retraso_salida_horas"].round(2).astype(float).tolist(),
        rows=result.round(2).to_dict(orient="records"),
    )


def get_cancelaciones_por_aerolinea(filters: dict | None = None) -> ChartDataResponse:
    """Porcentaje de cancelaciones por aerolínea."""
    df = get_filtered_fact(filters, copy=False)
    if df.empty:
        return _empty_chart()

    slim = pd.DataFrame({
        "_airline":   _label_series(df, ["Airline", "Operating_Airline", "Marketing_Airline"], "Sin aerolínea"),
        "_cancelled": _numeric(df, "Cancelled").fillna(0),
    })

    result = (
        slim.groupby("_airline", as_index=False)["_cancelled"]
        .mean()
        .rename(columns={"_airline": "aerolinea", "_cancelled": "cancelaciones_pct"})
        .assign(cancelaciones_pct=lambda x: x["cancelaciones_pct"] * 100)
        .sort_values("cancelaciones_pct", ascending=False)
    )

    return ChartDataResponse(
        labels=result["aerolinea"].tolist(),
        data=result["cancelaciones_pct"].round(2).astype(float).tolist(),
        rows=result.round(2).to_dict(orient="records"),
    )


def get_retraso_mensual(filters: dict | None = None) -> ChartDataResponse:
    """Evolución mensual de retrasos promedio de salida y llegada."""
    df = get_filtered_fact(filters, copy=False)
    if df.empty or "Month" not in df.columns:
        return _empty_chart()

    _month     = pd.to_numeric(df["Month"], errors="coerce")
    _dep_delay = _numeric(df, "DepDelayMinutes")
    _arr_delay = _numeric(df, "ArrDelayMinutes")

    df = pd.DataFrame({
        "_month":     _month,
        "_dep_delay": _dep_delay,
        "_arr_delay": _arr_delay,
    })

    result = (
        df.dropna(subset=["_month"])
        .groupby("_month", as_index=False)
        .agg(
            retraso_salida_promedio=("_dep_delay", "mean"),
            retraso_llegada_promedio=("_arr_delay", "mean"),
            total_vuelos=("_month", "size"),
        )
        .sort_values("_month")
    )
    result["mes"] = result["_month"].astype(int).map(_month_label)

    return ChartDataResponse(
        labels=result["mes"].tolist(),
        datasets=[
            {
                "label": "Retraso salida promedio",
                "data": result["retraso_salida_promedio"].round(2).astype(float).tolist(),
            },
            {
                "label": "Retraso llegada promedio",
                "data": result["retraso_llegada_promedio"].round(2).astype(float).tolist(),
            },
        ],
        rows=result.drop(columns=["_month"]).round(2).to_dict(orient="records"),
    )


def get_rutas_criticas(filters: dict | None = None) -> ChartDataResponse:
    """Rutas origen-destino con mayor retraso acumulado de salida."""
    df = get_filtered_fact(filters, copy=False)
    if df.empty:
        return _empty_chart()

    top_n = _top_n_from_filters(filters, default=15)
    origin_col = _first_existing(df, ["Origin", "Origin_ruta"])
    dest_col = _first_existing(df, ["Dest", "Dest_ruta"])
    if origin_col is None or dest_col is None:
        return _empty_chart()

    _origin = df[origin_col].fillna("Sin origen").astype(str)
    _dest   = df[dest_col].fillna("Sin destino").astype(str)
    df = pd.DataFrame({
        "_ruta":      _origin + " → " + _dest,
        "_dep_delay": _numeric(df, "DepDelayMinutes").fillna(0),
        "_arr_delay": _numeric(df, "ArrDelayMinutes"),
        "_cancelled": _numeric(df, "Cancelled").fillna(0),
    })

    result = (
        df.groupby("_ruta", as_index=False)
        .agg(
            retraso_salida_minutos=("_dep_delay", "sum"),
            retraso_llegada_promedio=("_arr_delay", "mean"),
            cancelaciones_pct=("_cancelled", "mean"),
            total_vuelos=("_ruta", "size"),
        )
        .rename(columns={"_ruta": "ruta"})
        .sort_values("retraso_salida_minutos", ascending=False)
        .head(top_n)
    )
    result["retraso_salida_horas"] = result["retraso_salida_minutos"] / 60
    result["cancelaciones_pct"] = result["cancelaciones_pct"] * 100

    return ChartDataResponse(
        labels=result["ruta"].tolist(),
        data=result["retraso_salida_horas"].round(2).astype(float).tolist(),
        rows=result.round(2).to_dict(orient="records"),
    )


def get_distribucion_vuelos(filters: dict | None = None) -> ChartDataResponse:
    """Distribución operacional: puntual, retrasado, cancelado y desviado."""
    df = get_filtered_fact(filters, copy=False)
    if df.empty:
        return _empty_chart()

    arr_delay = _numeric(df, "ArrDelayMinutes")
    cancelled = _numeric(df, "Cancelled").fillna(0)
    diverted = _numeric(df, "Diverted").fillna(0)

    cancelados = int((cancelled == 1).sum())
    desviados = int((diverted == 1).sum())
    retrasados = int(((arr_delay > 15) & (cancelled != 1) & (diverted != 1)).sum())
    puntuales = int(((arr_delay <= 15) & (cancelled != 1) & (diverted != 1)).sum())

    labels = ["Puntuales", "Retrasados > 15 min", "Cancelados", "Desviados"]
    data = [puntuales, retrasados, cancelados, desviados]
    total = sum(data) or 1
    rows = [
        {"categoria": label, "vuelos": value, "porcentaje": round(value / total * 100, 2)}
        for label, value in zip(labels, data)
    ]

    return ChartDataResponse(labels=labels, data=data, rows=rows)


# ============================================================
# Tabla
# ============================================================

def get_tabla_vuelos(filters: dict | None = None) -> TableResponse:
    """Tabla compacta para explorar vuelos filtrados."""
    filters = filters or {}
    limit = _top_n_from_filters(filters, default=500, max_n=5000)
    df = get_filtered_fact(filters, copy=False)

    if df.empty:
        return TableResponse(rows=[])

    preferred_cols = [
        "Year", "Month", "FlightDate",
        "Airline", "Origin", "OriginCityName", "Dest", "DestCityName",
        "DepDelayMinutes", "ArrDelayMinutes", "AirTime", "Distance",
        "Cancelled", "Diverted",
        "Tail_Number", "Flight_Number_Marketing_Airline", "Flight_Number_Operating_Airline",
    ]
    cols = [col for col in preferred_cols if col in df.columns]
    if not cols:
        cols = df.columns.tolist()[:20]

    out = df[cols].head(limit).copy()
    out = out.where(pd.notna(out), None)
    return TableResponse(rows=out.to_dict(orient="records"))