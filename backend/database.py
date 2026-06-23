from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

# ============================================================
# Configuración
# ============================================================
# Por defecto se asume esta estructura:
# /
# ├── backend/database.py
# └── datamart/
#     ├── fact_vuelos/fact_vuelos.parquet
#     ├── dim_fecha/dim_fecha.parquet
#     └── ...
#
# Puedes cambiar la ruta con variable de entorno:
#   DATAMART_DIR=/ruta/a/datamart

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATAMART_DIR = Path(os.getenv("DATAMART_DIR", PROJECT_ROOT / "datamart")).resolve()

# Columnas esperadas según el datamart del proyecto.
FACT_TABLE = "fact_vuelos"
DIM_TABLES = {
    "fecha": "dim_fecha",
    "hora": "dim_hora",
    "aerolinea": "dim_aerolinea",
    "avion": "dim_avion",
    "origen": "dim_origen",
    "destino": "dim_destino",
    "ruta": "dim_ruta",
    "vuelo": "dim_vuelo",
}


# ============================================================
# Utilidades generales
# ============================================================

def _norm_text(value: Any) -> str:
    """Normaliza texto para comparar valores de filtros."""
    if value is None:
        return ""
    text = str(value).strip().lower()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ä": "a", "ë": "e", "ï": "i", "ö": "o", "ü": "u",
        "ñ": "n",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return " ".join(text.split())


def to_int(value: Any) -> int | None:
    """Convierte valores de filtros a int cuando aplica."""
    if value in (None, "", "Todos", "Todas", "All"):
        return None
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return None


def to_float(value: Any) -> float | None:
    if value in (None, "", "Todos", "Todas", "All"):
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def to_bool(value: Any) -> bool | None:
    """Acepta true/false, 1/0, sí/no, cancelado/no cancelado, etc."""
    if value in (None, "", "Todos", "Todas", "All"):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(int(value))

    text = _norm_text(value)
    if text in {"1", "true", "t", "si", "sí", "yes", "y", "cancelado", "divertido", "delayed", "retrasado"}:
        return True
    if text in {"0", "false", "f", "no", "n", "no cancelado", "no divertido", "puntual", "on time"}:
        return False
    return None


def first_present(filters: dict[str, Any], keys: list[str]) -> Any | None:
    """Devuelve el primer filtro presente y no vacío."""
    for key in keys:
        value = filters.get(key)
        if value not in (None, "", "Todos", "Todas", "All"):
            return value
    return None


def _dedupe_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    return df.loc[:, ~df.columns.duplicated()].copy()


def _find_table_path(table_name: str) -> Path:
    """Encuentra el archivo/carpeta parquet de una tabla del datamart."""
    candidates = [
        DATAMART_DIR / table_name / f"{table_name}.parquet",
        DATAMART_DIR / table_name,
        DATAMART_DIR / f"{table_name}.parquet",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    raise FileNotFoundError(
        f"No se encontró la tabla '{table_name}' en {DATAMART_DIR}. "
        f"Se probaron rutas: {', '.join(str(c) for c in candidates)}"
    )


def read_parquet_table(table_name: str, columns: list[str] | None = None) -> pd.DataFrame:
    """Lee una tabla Parquet del datamart.

    Funciona tanto si la tabla está como archivo único .parquet como si está
    particionada dentro de una carpeta.
    """
    path = _find_table_path(table_name)
    df = pd.read_parquet(path, columns=columns)
    return _dedupe_columns(df)


def _safe_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _safe_int(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


# ============================================================
# Carga de datos en memoria
# ============================================================

print(f"🔄 Cargando datamart desde: {DATAMART_DIR}")

FACT_CACHE = read_parquet_table(FACT_TABLE)
DIM_FECHA = read_parquet_table(DIM_TABLES["fecha"])
DIM_HORA = read_parquet_table(DIM_TABLES["hora"])
DIM_AEROLINEA = read_parquet_table(DIM_TABLES["aerolinea"])
DIM_AVION = read_parquet_table(DIM_TABLES["avion"])
DIM_ORIGEN = read_parquet_table(DIM_TABLES["origen"])
DIM_DESTINO = read_parquet_table(DIM_TABLES["destino"])
DIM_RUTA = read_parquet_table(DIM_TABLES["ruta"])
DIM_VUELO = read_parquet_table(DIM_TABLES["vuelo"])

# Normalización de columnas numéricas comunes.
FACT_CACHE = _safe_numeric(
    FACT_CACHE,
    [
        "DepDelayMinutes", "ArrDelayMinutes", "AirTime", "Distance",
        "CRSElapsedTime", "ActualElapsedTime", "Cancelled", "Diverted",
        "DepDel15", "ArrDel15", "Dep15", "Arr15",
        "DepartureDelayGroups", "ArrivalDelayGroups",
    ],
)

FACT_CACHE = _safe_int(
    FACT_CACHE,
    [
        "fact_id", "dim_fecha_id", "dim_hora_id", "dim_hora_arr_id",
        "dim_aerolinea_id", "dim_avion_id", "dim_vuelo_id",
        "dim_origen_id", "dim_destino_id", "dim_ruta_id",
    ],
)

for dim_df, key in [
    (DIM_FECHA, "dim_fecha_id"),
    (DIM_HORA, "dim_hora_id"),
    (DIM_AEROLINEA, "dim_aerolinea_id"),
    (DIM_AVION, "dim_avion_id"),
    (DIM_ORIGEN, "dim_origen_id"),
    (DIM_DESTINO, "dim_destino_id"),
    (DIM_RUTA, "dim_ruta_id"),
    (DIM_VUELO, "dim_vuelo_id"),
]:
    _safe_int(dim_df, [key])

DIM_FECHA = _safe_int(DIM_FECHA, ["Year", "Quarter", "Month", "DayOfMonth", "DayOfWeek"])
DIM_HORA = _safe_int(DIM_HORA, ["hhmm", "Hora", "Minuto"])


# ============================================================
# Enriquecimiento mínimo de la fact table para filtrar rápido
# ============================================================

def _merge_dim_columns(
    fact: pd.DataFrame,
    dim: pd.DataFrame,
    key: str,
    columns: list[str],
    suffix: str | None = None,
) -> pd.DataFrame:
    available = [key] + [c for c in columns if c in dim.columns]
    if key not in fact.columns or key not in dim.columns or len(available) <= 1:
        return fact

    small_dim = dim[available].drop_duplicates(subset=[key]).copy()
    if suffix:
        rename_map = {c: f"{c}_{suffix}" for c in available if c != key and c in fact.columns}
        small_dim = small_dim.rename(columns=rename_map)

    return fact.merge(small_dim, on=key, how="left")


FACT_ENRICHED = FACT_CACHE.copy()

# Fecha: permite filtrar por año, mes y construir series temporales sin hacer joins en cada endpoint.
FACT_ENRICHED = _merge_dim_columns(
    FACT_ENRICHED,
    DIM_FECHA,
    "dim_fecha_id",
    ["FlightDate", "Year", "Quarter", "Month", "DayOfMonth", "DayOfWeek"],
)

# Hora de salida.
FACT_ENRICHED = _merge_dim_columns(
    FACT_ENRICHED,
    DIM_HORA,
    "dim_hora_id",
    ["hhmm", "Hora", "Minuto", "TimeBlock"],
)

# Aerolínea.
FACT_ENRICHED = _merge_dim_columns(
    FACT_ENRICHED,
    DIM_AEROLINEA,
    "dim_aerolinea_id",
    ["Airline", "Operating_Airline", "Marketing_Airline"],
)

# Origen / destino / ruta.
FACT_ENRICHED = _merge_dim_columns(
    FACT_ENRICHED,
    DIM_ORIGEN,
    "dim_origen_id",
    ["Origin", "OriginCityName", "OriginState", "OriginStateName"],
)
FACT_ENRICHED = _merge_dim_columns(
    FACT_ENRICHED,
    DIM_DESTINO,
    "dim_destino_id",
    ["Dest", "DestCityName", "DestState", "DestStateName"],
)
FACT_ENRICHED = _merge_dim_columns(
    FACT_ENRICHED,
    DIM_RUTA,
    "dim_ruta_id",
    ["Origin", "Dest", "DistanceGroup"],
    suffix="ruta",
)
FACT_ENRICHED = _merge_dim_columns(
    FACT_ENRICHED,
    DIM_AVION,
    "dim_avion_id",
    ["Tail_Number"],
)
FACT_ENRICHED = _merge_dim_columns(
    FACT_ENRICHED,
    DIM_VUELO,
    "dim_vuelo_id",
    ["Flight_Number_Marketing_Airline", "Flight_Number_Operating_Airline"],
)

print(
    f"✅ Fact cargada: {len(FACT_ENRICHED):,} filas "
    f"({FACT_ENRICHED.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB)"
)


# ============================================================
# Resolución de valores de filtros a IDs
# ============================================================

def value_to_dim_id(
    value: Any,
    dim: pd.DataFrame,
    id_col: str,
    match_cols: list[str],
) -> int | None:
    """Acepta ID directo, código o texto visible de una dimensión."""
    if value in (None, "", "Todos", "Todas", "All"):
        return None

    direct_id = to_int(value)
    if direct_id is not None and id_col in dim.columns:
        ids = set(pd.to_numeric(dim[id_col], errors="coerce").dropna().astype(int).tolist())
        if direct_id in ids:
            return direct_id

    text = str(value).strip()
    norm = _norm_text(text)

    for col in match_cols:
        if col not in dim.columns:
            continue
        series = dim[col].astype(str).fillna("")

        # Match exacto normalizado.
        mask = series.map(_norm_text) == norm
        matched = dim[mask]
        if not matched.empty:
            return int(matched.iloc[0][id_col])

        # Match parcial útil para labels tipo "AA - American Airlines".
        mask = series.map(lambda x: _norm_text(x) in norm or norm in _norm_text(x))
        matched = dim[mask]
        if not matched.empty:
            return int(matched.iloc[0][id_col])

    return direct_id


def normalize_filters(filters: dict[str, Any] | None) -> dict[str, Any]:
    """Unifica nombres de filtros que puede enviar el frontend.

    Acepta aliases defensivos para que el HTML pueda evolucionar sin romper
    el backend.
    """
    filters = filters or {}
    normalized: dict[str, Any] = {}

    anio = to_int(first_present(filters, ["anio", "year", "Year", "anio_id"])
)
    mes = to_int(first_present(filters, ["mes", "month", "Month", "mes_id"])
)
    mes_inicio = to_int(first_present(filters, ["mes_inicio", "month_start", "start_month", "mes_desde"])
)
    mes_fin = to_int(first_present(filters, ["mes_fin", "month_end", "end_month", "mes_hasta"])
)

    aerolinea_raw = first_present(
        filters,
        ["aerolinea", "airline", "Airline", "dim_aerolinea_id", "carrier", "operating_airline"],
    )
    origen_raw = first_present(
        filters,
        ["origen", "origin", "Origin", "dim_origen_id", "airport_origin", "aeropuerto_origen"],
    )
    destino_raw = first_present(
        filters,
        ["destino", "dest", "Dest", "dim_destino_id", "airport_dest", "aeropuerto_destino"],
    )
    ruta_raw = first_present(
        filters,
        ["ruta", "route", "dim_ruta_id", "origin_dest", "origen_destino"],
    )
    hora_raw = first_present(
        filters,
        ["hora", "hour", "Hora", "dim_hora_id", "time_block", "TimeBlock", "bloque_horario"],
    )
    avion_raw = first_present(filters, ["avion", "tail_number", "Tail_Number", "dim_avion_id"])
    vuelo_raw = first_present(filters, ["vuelo", "flight", "flight_number", "dim_vuelo_id"])

    aerolinea = value_to_dim_id(
        aerolinea_raw,
        DIM_AEROLINEA,
        "dim_aerolinea_id",
        ["Airline", "Operating_Airline", "Marketing_Airline"],
    )
    origen = value_to_dim_id(
        origen_raw,
        DIM_ORIGEN,
        "dim_origen_id",
        ["Origin", "OriginCityName", "OriginState", "OriginStateName"],
    )
    destino = value_to_dim_id(
        destino_raw,
        DIM_DESTINO,
        "dim_destino_id",
        ["Dest", "DestCityName", "DestState", "DestStateName"],
    )
    ruta = value_to_dim_id(
        ruta_raw,
        DIM_RUTA,
        "dim_ruta_id",
        ["Origin", "Dest", "DistanceGroup"],
    )
    hora = value_to_dim_id(
        hora_raw,
        DIM_HORA,
        "dim_hora_id",
        ["hhmm", "Hora", "TimeBlock"],
    )
    avion = value_to_dim_id(avion_raw, DIM_AVION, "dim_avion_id", ["Tail_Number"])
    vuelo = value_to_dim_id(
        vuelo_raw,
        DIM_VUELO,
        "dim_vuelo_id",
        ["Flight_Number_Marketing_Airline", "Flight_Number_Operating_Airline"],
    )

    cancelado = to_bool(first_present(filters, ["cancelado", "cancelled", "Cancelled", "is_cancelled"])
)
    divertido = to_bool(first_present(filters, ["desviado", "diverted", "Diverted", "is_diverted"])
)
    delayed15 = to_bool(first_present(filters, ["delayed15", "Delayed15", "dep15", "DepDel15", "retrasado15"])
)

    if anio is not None:
        normalized["anio"] = anio
    if mes is not None:
        normalized["mes"] = mes
    if mes_inicio is not None:
        normalized["mes_inicio"] = mes_inicio
    if mes_fin is not None:
        normalized["mes_fin"] = mes_fin

    if aerolinea is not None:
        normalized["aerolinea"] = aerolinea
    if origen is not None:
        normalized["origen"] = origen
    if destino is not None:
        normalized["destino"] = destino
    if ruta is not None:
        normalized["ruta"] = ruta
    if hora is not None:
        normalized["hora"] = hora
    if avion is not None:
        normalized["avion"] = avion
    if vuelo is not None:
        normalized["vuelo"] = vuelo

    if cancelado is not None:
        normalized["cancelado"] = cancelado
    if divertido is not None:
        normalized["divertido"] = divertido
    if delayed15 is not None:
        normalized["delayed15"] = delayed15

    return normalized


# ============================================================
# Filtro principal del datamart
# ============================================================

def get_filtered_fact(filters: dict[str, Any] | None, *, copy: bool = True) -> pd.DataFrame:
    """Filtra la tabla de hechos enriquecida según los filtros activos."""
    f = normalize_filters(filters)
    df = FACT_ENRICHED

    if f.get("anio") is not None and "Year" in df.columns:
        df = df[df["Year"] == f["anio"]]

    if f.get("mes") is not None and "Month" in df.columns:
        df = df[df["Month"] == f["mes"]]

    if f.get("mes_inicio") is not None and "Month" in df.columns:
        df = df[df["Month"] >= f["mes_inicio"]]

    if f.get("mes_fin") is not None and "Month" in df.columns:
        df = df[df["Month"] <= f["mes_fin"]]

    if f.get("aerolinea") is not None and "dim_aerolinea_id" in df.columns:
        df = df[df["dim_aerolinea_id"] == f["aerolinea"]]

    if f.get("origen") is not None and "dim_origen_id" in df.columns:
        df = df[df["dim_origen_id"] == f["origen"]]

    if f.get("destino") is not None and "dim_destino_id" in df.columns:
        df = df[df["dim_destino_id"] == f["destino"]]

    if f.get("ruta") is not None and "dim_ruta_id" in df.columns:
        df = df[df["dim_ruta_id"] == f["ruta"]]

    if f.get("hora") is not None and "dim_hora_id" in df.columns:
        df = df[df["dim_hora_id"] == f["hora"]]

    if f.get("avion") is not None and "dim_avion_id" in df.columns:
        df = df[df["dim_avion_id"] == f["avion"]]

    if f.get("vuelo") is not None and "dim_vuelo_id" in df.columns:
        df = df[df["dim_vuelo_id"] == f["vuelo"]]

    if f.get("cancelado") is not None and "Cancelled" in df.columns:
        df = df[df["Cancelled"].fillna(0).astype(int) == int(f["cancelado"])]

    if f.get("divertido") is not None and "Diverted" in df.columns:
        df = df[df["Diverted"].fillna(0).astype(int) == int(f["divertido"])]

    if f.get("delayed15") is not None:
        delayed_value = int(f["delayed15"])
        if "Delayed15" in df.columns:
            df = df[df["Delayed15"].fillna(0).astype(int) == delayed_value]
        elif "DepDel15" in df.columns:
            df = df[df["DepDel15"].fillna(0).astype(int) == delayed_value]
        elif "Dep15" in df.columns:
            df = df[df["Dep15"].fillna(0).astype(int) == delayed_value]
        elif "DepDelayMinutes" in df.columns:
            df = df[(df["DepDelayMinutes"].fillna(0) > 15).astype(int) == delayed_value]

    return df.copy() if copy else df


# ============================================================
# Helpers para opciones de filtros
# ============================================================

def get_year_options() -> list[list[Any]]:
    if "Year" not in DIM_FECHA.columns:
        return []
    values = pd.to_numeric(DIM_FECHA["Year"], errors="coerce").dropna().astype(int).drop_duplicates()
    return [[int(v), int(v)] for v in sorted(values.tolist(), reverse=True)]


def get_month_options() -> list[list[Any]]:
    if "Month" not in DIM_FECHA.columns:
        return []
    month_names = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Setiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
    }
    values = pd.to_numeric(DIM_FECHA["Month"], errors="coerce").dropna().astype(int).drop_duplicates()
    return [[int(v), month_names.get(int(v), str(v))] for v in sorted(values.tolist())]


def dim_options(dim: pd.DataFrame, id_col: str, label_cols: list[str], ids: list[Any] | None = None) -> list[list[Any]]:
    """Devuelve opciones tipo [[id, label], ...] para selects del frontend."""
    if dim is None or dim.empty or id_col not in dim.columns:
        return []

    out = dim.copy()
    if ids is not None:
        valid_ids = set(pd.Series(ids).dropna().astype(int).tolist())
        out = out[pd.to_numeric(out[id_col], errors="coerce").astype("Int64").isin(valid_ids)]

    label_cols = [c for c in label_cols if c in out.columns]
    if not label_cols:
        label_cols = [id_col]

    def build_label(row: pd.Series) -> str:
        values = [str(row.get(c, "")).strip() for c in label_cols if str(row.get(c, "")).strip()]
        return " - ".join(dict.fromkeys(values)) if values else str(row[id_col])

    out["_label"] = out.apply(build_label, axis=1)
    out = out[[id_col, "_label"]].drop_duplicates().sort_values("_label")
    return [[int(row[id_col]), row["_label"]] for _, row in out.iterrows()]
