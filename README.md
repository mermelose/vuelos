# 🚀 Vuelos Big Data

Esta aplicación es el motor centralizado de una plataforma de **Business Intelligence (BI)**. Integra una capa de datos (**Datamart**), un modelo analítico predictivo entrenado en **Apache Spark (MLlib)** y una **API REST (FastAPI)** que unifica ambos mundos para servir métricas y predicciones en tiempo real a los tableros de visualización.

## 📋 Arquitectura del Proyecto (4 Capas)

El sistema está estructurado bajo una arquitectura limpia dividida en las siguientes capas:

1. **Capa de Presentación (Página Web / Frontend):** Interfaz web y dashboards interactivos donde el usuario final visualiza los reportes de BI y consume las predicciones en tiempo real.
2. **Capa de Servicio (API REST):** Construida con **FastAPI**, actúa como el cerebro del sistema. Conecta la interfaz web con el Datamart y ejecuta el modelo de Machine Learning.
3. **Capa Analítica (Machine Learning):** Modelo predictivo nativo de **Spark ML** alojado directamente en la API para realizar scoring/predicciones al vuelo.
4. **Capa de Datos (Datamart):** Base de datos relacional optimizada para consultas analíticas agregadas que alimenta tanto a la interfaz web como al reentrenamiento del modelo.


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

---

## ⚡ Ejecutar la API

Para iniciar el servidor local de FastAPI y empezar a recibir peticiones de predicción, ejecuta:

```bash
uvicorn src.app.main:app --reload

```

* **API local disponible en:** `http://127.0.0.1:8000`
* **Documentación interactiva (Swagger UI):** `http://127.0.0.1:8000/docs`

---

## 🧠 Estructura de los Endpoints

### `POST /predict`

Envía los datos de entrada para obtener la predicción generada por el modelo de Spark.

* **Cuerpo de la petición (JSON de ejemplo):**

```json
    {
      "features": [5.1, 3.5, 1.4, 0.2]
    }
    ```

* **Respuesta del servidor (200 OK):**
```json
    {
      "prediction": 1.0
    }
    ```

---

## 📁 Estructura del Proyecto

```text
├── models/
│   └── mi_modelo_spark/  # Carpeta del modelo exportado por Spark ML
├── src/
│   ├── app/
│   │   └── main.py       # API REST con FastAPI (Carga el modelo y predice)
│   └── train.py          # Script de PySpark para entrenar y guardar el modelo
├── requirements.txt      # Librerías de Python requeridas
└── README.md             # Este archivo informativo

```

---

## ✒️ Autor

* **Paolo Salazar** - *Desarrollo e Implementación* 
* **Cynthia Zhou** - *Desarrollo e Implementación*
* **Fabrizio Montalvo** - *Desarrollo e Implementación*
* **Maricarmen Mendoza** - *Desarrollo e Implementación* 
```

```
