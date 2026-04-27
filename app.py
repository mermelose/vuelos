import streamlit as st
import pandas as pd
import plotly.express as px
import glob

st.set_page_config(page_title="✈️ Vuela Alto Fabo", layout="wide", page_icon="✈️")

BASE_PATH = "datamart"
SAMPLE_SIZE = 5000

# ----------------------- CARGA -----------------------------
@st.cache_data
def load_tables():
    fact_files = glob.glob(f"{BASE_PATH}/fact_vuelos/*.parquet")

    dfs = []
    for f in fact_files:
        df = pd.read_parquet(f)
        if len(df) > SAMPLE_SIZE:
            df = df.sample(SAMPLE_SIZE, random_state=42)
        dfs.append(df)

    fact = pd.concat(dfs, ignore_index=True)

    dims = {
        "aerolinea": pd.read_parquet(f"{BASE_PATH}/dim_aerolinea/dim_aerolinea.parquet"),
        "origen": pd.read_parquet(f"{BASE_PATH}/dim_origen/dim_origen.parquet"),
        "destino": pd.read_parquet(f"{BASE_PATH}/dim_destino/dim_destino.parquet"),
        "fecha": pd.read_parquet(f"{BASE_PATH}/dim_fecha/dim_fecha.parquet")
    }

    return fact, dims

fact, dims = load_tables()

# ----------------------- BASE PARA FILTROS -----------------------------
def build_filter_base(fact, dims):
    df = fact.merge(dims["aerolinea"], on="dim_aerolinea_id", how="inner")
    df = df.merge(dims["origen"], on="dim_origen_id", how="inner")
    df = df.merge(dims["destino"], on="dim_destino_id", how="inner")

    df = df.rename(columns={
        "DepDelayMinutes": "DepDelay",
        "ArrDelayMinutes": "ArrDelay"
    })

    return df

base_df = build_filter_base(fact, dims)

# ----------------------- SIDEBAR -----------------------------
st.sidebar.title("🔍 Filtros")
aerolineas = st.sidebar.multiselect("Aerolínea", base_df["Airline"].unique())
origenes = st.sidebar.multiselect("Origen", base_df["Origin"].unique())
destinos = st.sidebar.multiselect("Destino", base_df["Dest"].unique())


def apply_user_filters(df):
    if aerolineas:
        df = df[df["Airline"].isin(aerolineas)]
    if origenes:
        df = df[df["Origin"].isin(origenes)]
    if destinos:
        df = df[df["Dest"].isin(destinos)]
    return df

# ------------------------ TABS --------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Resumen Ejecutivo",
    "✈️ Puntualidad y Retrasos",
    "🛫 Aeropuertos Críticos",
    "❌ Cancelaciones y Disrupciones"
])

# =====================================================================
# TAB 1
# =====================================================================
with tab1:
    st.header("🏠 Resumen Ejecutivo del Desempeño Operacional")
    df = apply_user_filters(base_df.copy())

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Retraso salida promedio", f"{df['DepDelay'].mean():.1f} min")
    col2.metric("Retraso llegada promedio", f"{df['ArrDelay'].mean():.1f} min")
    col3.metric("OTP", f"{((df['ArrDelay'] <= 15).mean()*100):.1f} %")
    col4.metric("Cancelaciones", f"{(df['Cancelled'].mean()*100):.1f} %")

    st.dataframe(df.head(2000))

# =====================================================================
# TAB 2
# =====================================================================
with tab2:
    st.header("✈️ Análisis de Puntualidad por Aerolínea")
    df = fact.merge(dims["aerolinea"], on="dim_aerolinea_id", how="inner")
    df = df.rename(columns={"ArrDelayMinutes": "ArrDelay"})
    df = df.merge(dims["origen"], on="dim_origen_id", how="inner")
    df = df.merge(dims["destino"], on="dim_destino_id", how="inner")

    df = apply_user_filters(df)

    airline_delay = df.groupby("Airline")["ArrDelay"].mean().reset_index()

    order = airline_delay.sort_values("ArrDelay")["Airline"].tolist()[::-1]

    fig = px.bar(
        airline_delay.sort_values("ArrDelay"),
        x="ArrDelay",
        y="Airline",
        orientation="h",
        labels={
            "ArrDelay": "Retraso promedio llegada (min)",
            "Airline": "Aerolínea"
        },
        category_orders={"Airline": order}
    )

    st.plotly_chart(fig, use_container_width=True)

# =====================================================================
# TAB 3
# =====================================================================
with tab3:
    st.header("🛫 Aeropuertos con Mayor Retraso")
    df = fact.merge(dims["origen"], on="dim_origen_id", how="inner")
    df = df.rename(columns={"DepDelayMinutes": "DepDelay"})
    df = df.merge(dims["aerolinea"], on="dim_aerolinea_id", how="inner")
    df = df.merge(dims["destino"], on="dim_destino_id", how="inner")

    df = apply_user_filters(df)

    airport_delay = (
        df.groupby("Origin")["DepDelay"]
        .sum()
        .reset_index()
        .sort_values("DepDelay", ascending=False)
        .head(15)
    )

    airport_delay["DelayHours"] = airport_delay["DepDelay"] / 60

    order = airport_delay.sort_values("DelayHours")["Origin"].tolist()[::-1]

    fig = px.bar(
        airport_delay.sort_values("DelayHours"),
        x="DelayHours",
        y="Origin",
        orientation="h",
        labels={
            "DelayHours": "Horas de retraso acumulado",
            "Origin": "Aeropuerto"
        },
        category_orders={"Origin": order}
    )

    st.plotly_chart(fig, use_container_width=True)
# =====================================================================
# TAB 4
# =====================================================================
with tab4:
    st.header("❌ Cancelaciones y Disrupciones")
    df = fact.merge(dims["aerolinea"], on="dim_aerolinea_id", how="inner")
    df = df.rename(columns={"ArrDelayMinutes": "ArrDelay"})
    df = df.merge(dims["origen"], on="dim_origen_id", how="inner")
    df = df.merge(dims["destino"], on="dim_destino_id", how="inner")

    df = apply_user_filters(df)

    cancel = df.groupby("Airline")["Cancelled"].mean().reset_index()
    cancel["Cancelled"] *= 100

    order = cancel.sort_values("Cancelled")["Airline"].tolist()[::-1]

    fig = px.bar(
        cancel.sort_values("Cancelled"),
        x="Cancelled",
        y="Airline",
        orientation="h",
        labels={
            "Cancelled": "% cancelaciones",
            "Airline": "Aerolínea"
        },
        category_orders={"Airline": order}
    )

    st.plotly_chart(fig, use_container_width=True)

    df["Affected"] = (
        (df["ArrDelay"] > 15) |
        (df["Cancelled"] == 1) |
        (df["Diverted"] == 1)
    )

    st.metric("Vuelos afectados", f"{df['Affected'].mean()*100:.1f} %")
