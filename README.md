# ✈️ Flight Delay Analytics Datamart

## 1. Descripción

Este repositorio implementa un datamart dimensional basado en datos históricos de vuelos (2018 a 2022). El objetivo es analizar puntualidad, retrasos, cancelaciones y desempeño operacional mediante un dashboard interactivo.

El proyecto sigue un enfoque de Business Intelligence sobre un esquema estrella optimizado para consultas analíticas.

---

## 2. Estructura del repositorio

```
/
├── app.py
├── datamart_flights_databricks_orc.ipynb
├── requirements.txt
└── datamart/
    ├── dim_aerolinea/
    ├── dim_avion/
    ├── dim_destino/
    ├── dim_fecha/
    ├── dim_hora/
    ├── dim_origen/
    ├── dim_ruta/
    ├── dim_vuelo/
    └── fact_vuelos/
```

---

## 3. Dataset

Fuente: Flight Delay Dataset 2018–2022

Acceso:
https://drive.google.com/drive/folders/1CF7CDKkXqdKbD1jDnxES2CT8WT85z97C

Contenido:

* Datos históricos de vuelos
* Horarios programados y reales
* Retrasos, cancelaciones y desvíos
* Información de aerolíneas, rutas y aeropuertos

---

## 4. Modelo de datos

Se utiliza un esquema estrella.

### Tabla de hechos

fact_vuelos

Contiene métricas operativas:

* retrasos
* tiempos de vuelo
* cancelaciones
* desvíos

Claves:

* dim_fecha_id
* dim_hora_id
* dim_avion_id
* dim_vuelo_id
* dim_origen_id
* dim_destino_id
* dim_ruta_id
* dim_aerolinea_id

Métricas principales:

* DepDelayMinutes
* ArrDelayMinutes
* AirTime
* Distance
* Cancelled
* Diverted

---

### Dimensiones

dim_aerolinea

* Airline
* dim_aerolinea_id

dim_avion

* Tail_Number
* dim_avion_id

dim_destino

* Dest
* DestCityName
* DestState
* DestStateName
* dim_destino_id

dim_fecha

* FlightDate
* Year
* Quarter
* Month
* DayOfMonth
* DayOfWeek
* dim_fecha_id

dim_hora

* hhmm
* Hora
* Minuto
* TimeBlock
* dim_hora_id

dim_origen

* Origin
* OriginCityName
* OriginState
* OriginStateName
* dim_origen_id

dim_ruta

* Origin
* Dest
* DistanceGroup
* dim_ruta_id

dim_vuelo

* Flight_Number_Marketing_Airline
* Flight_Number_Operating_Airline
* dim_vuelo_id

---

## 5. Pipeline de datos

Flujo:

1. Ingesta
   Descarga y carga del dataset original

2. Transformación
   Limpieza, tipificación y normalización

3. Modelado
   Construcción del esquema estrella

4. Almacenamiento
   Archivos en formato Parquet

---

## 6. Dashboard

Archivo: app.py
Framework: Streamlit

### Funcionalidades

Filtros:

* Aerolínea
* Origen
* Destino

Tabs:

1. Resumen Ejecutivo

   * Retraso promedio salida
   * Retraso promedio llegada
   * OTP
   * % cancelaciones

2. Puntualidad por aerolínea

   * Ranking de retrasos promedio

3. Aeropuertos críticos

   * Retraso acumulado por origen

4. Cancelaciones y disrupciones

   * % cancelaciones por aerolínea
   * % vuelos afectados

---

## 7. Ejecución

### 1. Instalar dependencias

```
pip install -r requirements.txt
```

### 2. Ejecutar aplicación

```
streamlit run app.py
```

---

## 8. Decisiones técnicas

* Formato Parquet para eficiencia en lectura
* Muestreo de datos para mejorar rendimiento en dashboard
* Uso de pandas para ETL
* Visualización con Plotly
* Caché con Streamlit para evitar recargas innecesarias

---

## 9. KPIs implementados

* On-Time Performance (OTP)
* Retraso promedio
* Retraso acumulado
* Tasa de cancelación
* Vuelos afectados

---
