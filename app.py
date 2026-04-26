import streamlit as st
import pandas as pd
import altair as alt
import requests

st.set_page_config(
    page_title="Vuela Alto Fabo — Dashboard de Vuelos",
    layout="wide",
    page_icon="✈️"
)

API_URL = "https://could-earth-labor-late.trycloudflare.com/data"

# ----------------------- CARGA DE DATOS -----------------------------
@st.cache_data
def load_data():
    response = requests.get(API_URL, timeout=20)
    response.raise_for_status()
    df = pd.DataFrame(response.json())

    # Corrección de tipos
    if "FlightDate" in df.columns:
        df["FlightDate"] = pd.to_datetime(df["FlightDate"], errors="coerce")

    df = df.fillna({"DepDelay": 0, "ArrDelay": 0, "Cancelled": 0, "Diverted": 0})
    return df


df = load_data()

# Sidebar
st.sidebar.title("🔍 Filtros")
aerolineas = st.sidebar.multiselect("Aerolínea", df["Airline"].unique())
origenes = st.sidebar.multiselect("Origen", df["Origin"].unique())
destinos = st.sidebar.multiselect("Destino", df["Dest"].unique())

df_filt = df.copy()
if aerolineas:
    df_filt = df_filt[df_filt["Airline"].isin(aerolineas)]
if origenes:
    df_filt = df_filt[df_filt["Origin"].isin(origenes)]
if destinos:
    df_filt = df_filt[df_filt["Dest"].isin(destinos)]

# ------------------------ TABS PRINCIPALES --------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🏠 Resumen Ejecutivo",
    "✈️ Puntualidad y Retrasos",
    "🛫 Aeropuertos Críticos",
    "❌ Cancelaciones y Disrupciones"
])

# =====================================================================
# TAB 1 — RESUMEN EJECUTIVO
# =====================================================================
with tab1:
    st.header("🏠 Resumen Ejecutivo del Desempeño Operacional")

    col1, col2, col3, col4 = st.columns(4)

    prom_dep = df_filt["DepDelay"].mean()
    prom_arr = df_filt["ArrDelay"].mean()
    otp = (df_filt["ArrDelay"] <= 15).mean() * 100
    cancel_rate = df_filt["Cancelled"].mean() * 100

    col1.metric("Retraso Prom. Despegue", f"{prom_dep:.2f} min")
    col2.metric("Retraso Prom. Llegada", f"{prom_arr:.2f} min")
    col3.metric("OTP (On-Time Performance)", f"{otp:.2f}%")
    col4.metric("Tasa de Cancelación", f"{cancel_rate:.2f}%")

    st.markdown("""
    ### Preguntas de Negocio que responde este dashboard
    - **¿Qué aerolíneas exhiben mejor puntualidad?**  
    - **¿Qué aeropuertos acumulan más minutos de demora?**  
    - **¿Cuál es la tasa de cancelación promedio por aerolínea, mes y aeropuerto?**  

    ### Decisiones Operativas que habilita
    - Ajustar programación en rutas de bajo desempeño.  
    - Incrementar buffers de giro en aeropuertos congestionados.  
    - Optimizar asignación de flota en horarios críticos.  
    - Focalizar iniciativas de mejora en aerolíneas con mal rendimiento.  
    """)

    with st.expander("📄 Datos filtrados"):
        st.dataframe(df_filt)

# =====================================================================
# TAB 2 — PUNTUALIDAD Y RETRASOS
# =====================================================================
with tab2:
    st.header("✈️ Análisis de Puntualidad y Retrasos por Aerolínea")

    airline_delay = (
        df_filt.groupby("Airline")["ArrDelay"]
        .mean()
        .reset_index()
        .sort_values("ArrDelay")
    )

    chart_delay = (
        alt.Chart(airline_delay)
        .mark_bar()
        .encode(
            x=alt.X("ArrDelay", title="Retraso promedio (min)"),
            y=alt.Y("Airline", sort="-x", title="Aerolínea"),
            color=alt.Color("ArrDelay", scale=alt.Scale(scheme="blues"))
        )
    )

    st.altair_chart(chart_delay, use_container_width=True)

    otp_airline = (
        (df_filt["ArrDelay"] <= 15)
        .groupby(df_filt["Airline"])
        .mean()
        .reset_index(name="OTP")
        .sort_values("OTP", ascending=False)
    )

    st.subheader("⭐ Aerolíneas con Mejor OTP")

    chart_otp = (
        alt.Chart(otp_airline)
        .mark_bar()
        .encode(
            x=alt.X("OTP", title="OTP (%)", axis=alt.Axis(format=".0%")),
            y=alt.Y("Airline", sort="-x"),
            color=alt.Color("OTP", scale=alt.Scale(scheme="greens"))
        )
    )

    st.altair_chart(chart_otp, use_container_width=True)

# =====================================================================
# TAB 3 — AEROPUERTOS CRÍTICOS
# =====================================================================
with tab3:
    st.header("🛫 Aeropuertos con Mayor Retraso Acumulado")

    airport_delay = (
        df_filt.groupby("Origin")["DepDelay"]
        .sum()
        .reset_index()
        .sort_values("DepDelay", ascending=False)
        .head(15)
    )

    chart_airport = (
        alt.Chart(airport_delay)
        .mark_bar()
        .encode(
            x=alt.X("DepDelay", title="Minutos de demora acumulada"),
            y=alt.Y("Origin", sort="-x"),
            color=alt.Color("DepDelay", scale=alt.Scale(scheme="reds"))
        )
    )

    st.altair_chart(chart_airport, use_container_width=True)

    st.markdown("""
    ### Interpretación Operativa
    - Los aeropuertos superiores son candidatos para **aumentar buffers de giro**.  
    - Pueden tener restricciones en pista, clima o congestión.  
    """)

# =====================================================================
# TAB 4 — CANCELACIONES Y DISRUPCIONES
# =====================================================================
with tab4:
    st.header("❌ Cancelaciones y Disrupciones")

    cancel_by_airline = (
        df_filt.groupby("Airline")["Cancelled"]
        .mean()
        .reset_index()
    )
    cancel_by_airline["Cancelled"] *= 100

    chart_cancel = (
        alt.Chart(cancel_by_airline)
        .mark_bar()
        .encode(
            x=alt.X("Cancelled", title="% Cancelaciones"),
            y=alt.Y("Airline", sort="-x"),
            color=alt.Color("Cancelled", scale=alt.Scale(scheme="oranges"))
        )
    )
    st.altair_chart(chart_cancel, use_container_width=True)

    # KPI de vuelos afectados
    df_filt["Affected"] = (
        (df_filt["ArrDelay"] > 15) |
        (df_filt["Cancelled"] == 1) |
        (df_filt["Diverted"] == 1)
    )

    affected_rate = df_filt["Affected"].mean() * 100

    st.metric("Vuelos Afectados (Disrupciones)", f"{affected_rate:.2f}%")

    st.markdown("""
    ### Decisiones Recomendadas
    - Focalizar mejoras en aerolíneas con mayores tasas de cancelación.  
    - Revisar asignación de flota y slots en meses críticos.  
    - Implementar alertas automáticas para disrupciones.  
    """)

