# 🚀 Vuelos Big Data

Este proyecto es una aplicación integral de **Business Intelligence (BI)** y analítica predictiva para la gestión y análisis de datos de vuelos. El sistema implementa una arquitectura completa de 4 capas: procesamiento distribuido en **Apache Spark**, almacenamiento en un **Datamart** relacional, una **API REST (FastAPI)** y una **Interfaz Web** interactiva para el usuario final.

---

## 📋 Arquitectura del Sistema (4 Capas)

La plataforma está estructurada en base a los siguientes componentes distribuidos en el repositorio:

1. **Capa de Presentación (`frontend/`):** Interfaz web basada en `index.html` que consume los endpoints de la API para mostrar tableros analíticos, reportes de BI y permitir a los usuarios consultar predicciones de vuelos interactuando con formularios.
2. **Capa de Servicio (`backend/`):** API REST construida con **FastAPI**. Contiene la lógica de negocio (`services.py`), los contratos de datos (`schemas.py`), la conexión a la base de datos (`database.py`) y expone los puntos de acceso en `main.py`.
3. **Capa Analítica / ML (`modelo_vuelos_rf/`):** Modelo predictivo de tipo **Random Forest** entrenado con Spark ML. La API levanta una sesión local de PySpark para cargar los stages y metadata de este modelo, permitiendo realizar predicciones en tiempo real.
4. **Capa de Datos (`datamart/`):** Base de datos analítica diseñada bajo un modelo dimensional en estrella (Tablas de hechos `fact_vuelos` y dimensiones como `dim_aerolinea`, `dim_destino`, `dim_ruta`, etc.) optimizada para consultas de BI de alta velocidad.

---

## 🛠️ Requisitos Previos

Antes de ejecutar la aplicación, asegúrate de tener configurado:

* **Python 3.9 o superior**
* **Java JDK 11 o 17** (Requerido para la ejecución de PySpark en la API).
* **Acceso al Datamart:** Credenciales de la base de datos analítica.
* **Navegador Web moderno** (para acceder a la interfaz de usuario).

---
## 🚀 Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/mermelose/vuelos.git

```

2. **Crear y activar un entorno virtual:**

```bash
   python -m venv venv
   # En Windows:
   venv\Scripts\activate
   # En macOS/Linux:
   source venv/bin/activate

```

3. **Instalar las dependencias requeridas:**

```bash
   pip install -r requirements.txt

```

*(Asegúrate de que tu archivo `requirements.txt` incluya al menos: `pyspark`, `fastapi` y `uvicorn`)*

### 2. Pipeline de Datos y Reentrenamiento del Modelo (Opcional)

Si deseas reprocesar los datos en la nube o localmente para actualizar el modelo, cuentas con los siguientes notebooks y scripts en la raíz:

* `datamart_flights_databricks_orc.ipynb`: Notebook para procesamiento a gran escala en Databricks usando formato ORC.
* `datamart_flights_local_pandas.ipynb`: Procesamiento alternativo local usando Pandas.
* `ml_vuelos_spark_cluster_final.py`: Script principal de PySpark que entrena el Random Forest y exporta la carpeta `modelo_vuelos_rf/`.

### 3. Levantar el Backend (FastAPI + SparkML)

Para iniciar el servidor de la API que conecta al Datamart y monta el modelo predictivo, ejecuta desde la raíz:

```bash
uvicorn backend.main:app --reload

```

* **Documentación interactiva de Endpoints:** `http://127.0.0.1:8000/docs`

### 4. Abrir la Capa de Presentación (Frontend)

Navega a la carpeta `frontend/` y abre el archivo `index.html` en cualquier navegador web moderno, o configúralo para que sea servido como archivos estáticos a través de la misma API de FastAPI.

---

## 🔌 Endpoints Principales de la API

* **`GET /flights/analytics`:** Realiza consultas agregadas al Datamart (`fact_vuelos` unidos a las dimensiones) para extraer métricas de BI y alimentar los gráficos del frontend.
* **`POST /predict`:** Recibe los datos de un vuelo desde la interfaz web, los vectoriza y utiliza la sesión de PySpark para calcular la predicción utilizando el modelo Random Forest alojado en `modelo_vuelos_rf/`.

---

## 📁 Estructura Completa del Repositorio

```text
├── backend/                  # Código fuente de la API REST (FastAPI)
│   ├── database.py           # Configuración de la conexión al Datamart SQL
│   ├── main.py               # Endpoints y orquestación principal de la API
│   ├── schemas.py            # Modelos de validación Pydantic
│   └── services.py           # Lógica analítica y de negocio
├── datamart/                 # Estructura del Datamart dimensional de vuelos
│   ├── fact_vuelos/          # Tabla de hechos principal
│   ├── dim_aerolinea/        # Dimensión de aerolíneas
│   ├── dim_avion/            # Dimensión de aeronaves
│   ├── dim_destino/          # Dimensión de destinos
│   ├── dim_fecha/            # Dimensión temporal (Fechas)
│   ├── dim_hora/             # Dimensión temporal (Horas)
│   ├── dim_origen/           # Dimensión de orígenes
│   └── dim_ruta/             # Dimensión de rutas aéreas
├── frontend/                 # Capa de presentación (Página Web)
│   └── index.html            # Dashboard e interfaz web de BI
├── modelo_vuelos_rf/         # Modelo Random Forest guardado por Spark ML
│   ├── metadata/             # Metadatos del entrenamiento
│   └── stages/               # Fases y transformaciones del Pipeline de Spark
├── datamart_flights_databricks_orc.ipynb  # ETL y procesamiento en Databricks
├── datamart_flights_local_pandas.ipynb    # ETL alternativo local con Pandas
├── ml_vuelos_spark_cluster_final.py       # Script original de entrenamiento Spark
├── requirements.txt          # Dependencias del proyecto (pyspark, fastapi, uvicorn, etc.)
└── README.md                 # Este archivo descriptivo


---

## ✒️ Autor

* **Paolo Salazar** - *Desarrollo e Implementación* 
* **Cynthia Zhou** - *Desarrollo e Implementación*
* **Fabrizio Montalvo** - *Desarrollo e Implementación*
* **Maricarmen Mendoza** - *Desarrollo e Implementación* 
```

```
