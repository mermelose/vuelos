# ✈️ Flight Delay Analytics Datamart

## 1. Descripción

Este repositorio implementa un datamart dimensional basado en datos históricos de vuelos (2018 a 2022). Permite analizar puntualidad, retrasos, cancelaciones y desempeño operacional mediante un dashboard interactivo.

---

## 2. Estructura del repositorio

```
/
├── app.py
├── datamart_flights_databricks_orc.ipynb
├── requirements.txt
└── datamart/
    ├── dim_aerolinea/dim_aerolinea.parquet
    ├── dim_avion/dim_avion.parquet
    ├── dim_destino/dim_destino.parquet
    ├── dim_fecha/dim_fecha.parquet
    ├── dim_hora/dim_hora.parquet
    ├── dim_origen/dim_origen.parquet
    ├── dim_ruta/dim_ruta.parquet
    ├── dim_vuelo/dim_vuelo.parquet
    └── fact_vuelos/fact_vuelos.parquet
```

---

## 3. Dataset

Fuente: Flight Delay Dataset 2018–2022

Archivos originales:

* Combined_Flights_2018.parquet
* Combined_Flights_2019.parquet
* Combined_Flights_2020.parquet
* Combined_Flights_2021.parquet
* Combined_Flights_2022.parquet

Acceso:
https://drive.google.com/drive/folders/1CF7CDKkXqdKbD1jDnxES2CT8WT85z97C

---

## 4. Modelo de datos

Esquema estrella con una tabla de hechos y múltiples dimensiones.

### Tabla de hechos

fact_vuelos

Métricas:

* DepDelayMinutes
* ArrDelayMinutes
* AirTime
* Distance
* Cancelled
* Diverted

Claves:

* dim_fecha_id
* dim_hora_id
* dim_avion_id
* dim_vuelo_id
* dim_origen_id
* dim_destino_id
* dim_ruta_id
* dim_aerolinea_id

---

### Dimensiones

dim_aerolinea,
dim_avion,
dim_destino,
dim_fecha,
dim_hora,
dim_origen,
dim_ruta,
dim_vuelo

Cada dimensión contiene atributos descriptivos y su clave.

---

## 5. Pipeline de datos

Flujo:

1. Ingesta
2. Limpieza y transformación
3. Modelado dimensional
4. Almacenamiento en Parquet

---

## 6. Dashboard

Archivo: app.py
Framework: Streamlit

Tabs:

* Resumen Ejecutivo
* Puntualidad por aerolínea
* Aeropuertos críticos
* Cancelaciones y disrupciones

KPIs:

* OTP
* Retraso promedio
* Retraso acumulado
* % cancelaciones
* % vuelos afectados

---

## 7. Ejecución rápida

Instalar dependencias:

```
pip install -r requirements.txt
```

Ejecutar app:

```
streamlit run app.py
```

---

## 8. Sección opcional: generación del datamart desde cero

Usa esta sección si no tienes la carpeta datamart creada.

### Paso 1. Descargar dataset

Descarga los archivos desde Google Drive:

* Combined_Flights_2018.parquet
* Combined_Flights_2019.parquet
* Combined_Flights_2020.parquet
* Combined_Flights_2021.parquet
* Combined_Flights_2022.parquet

Guárdalos en una carpeta local o en tu entorno de Databricks.

---

### Paso 2. Ejecutar notebook en Databricks

Archivo:
datamart_flights_databricks_orc.ipynb

Acciones:

* Cargar los archivos Combined_Flights
* Ejecutar limpieza y transformación
* Construir dimensiones
* Construir tabla de hechos
* Exportar resultados en formato Parquet

Salida esperada:

```
datamart/
```

con todas las tablas:

* dimensiones
* fact_vuelos particionada

---

### Paso 3. Descargar datamart

Desde Databricks:

* Exportar la carpeta datamart
* Copiarla al root del proyecto

Estructura final requerida:

```
/datamart/...
```

---

### Paso 4. Ejecutar aplicación

Una vez que exista la carpeta datamart:

```
streamlit run app.py
```

---

