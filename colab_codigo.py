# Celda 1 - instalar todo
!pip install pyspark flask flask-ngrok pyngrok -q

from pyngrok import ngrok
from flask import Flask, request, jsonify
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel
import threading

spark = SparkSession.builder.master("local[*]").appName("Predict").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")

# Sube tu carpeta modelo_vuelos_rf a Google Drive y monta Drive
from google.colab import drive
drive.mount('/content/drive')

MODEL_PATH = "/content/drive/MyDrive/modelo_vuelos_rf"
model = PipelineModel.load(MODEL_PATH)

app = Flask(__name__)

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json  # recibe el caso como JSON
    caso = spark.createDataFrame([data])
    pred = model.transform(caso)
    resultado = pred.select("prediction", "probability").collect()[0]
    return jsonify({
        "prediction": resultado["prediction"],
        "probability": resultado["probability"].toArray().tolist()
    })

# Exponer con ngrok
public_url = ngrok.connect(5000)
print("URL pública:", public_url)

app.run(port=5000)