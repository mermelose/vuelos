# ml_vuelos_spark_cluster.py
# Ejecutar desde el master con:
# spark-submit --master yarn --deploy-mode client ml_vuelos_spark_cluster.py hdfs:///user/javier/dat/datamart
#
# Si tus Parquet NO están en HDFS sino copiados localmente en cada nodo:
# spark-submit --master yarn --deploy-mode client ml_vuelos_spark_cluster.py file:///home/javier/dat/datamart
#
# Recomendado: subir una sola vez a HDFS:
# hdfs dfs -mkdir -p /user/javier/dat/datamart
# hdfs dfs -put -f /home/javier/Descargas/dat/datamart/* /user/javier/dat/datamart/

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, desc, broadcast
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, BinaryClassificationEvaluator


# Cambia este default si tu ruta HDFS real es otra.
DATAMART_PATH = sys.argv[1] if len(sys.argv) > 1 else "hdfs:///user/javier/Descargas/dat/datamart"
MODEL_OUT = sys.argv[2] if len(sys.argv) > 2 else "hdfs:///user/javier/modelos/modelo_vuelos_rf"

spark = (
    SparkSession.builder
    .appName("ML_Vuelos_DepDelay_Spark_Cluster")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


def read_table(table_name: str):
    """Lee una carpeta parquet del datamart."""
    path = f"{DATAMART_PATH.rstrip('/')}/{table_name}"
    return spark.read.parquet(path)


# 1) Leer tablas Parquet del datamart en Hadoop/Spark
fact = read_table("fact_vuelos").alias("f")
dim_hora_dep = read_table("dim_hora").alias("dep")
dim_hora_arr = read_table("dim_hora").alias("arr")
dim_fecha = read_table("dim_fecha").alias("fe")
dim_aerolinea = read_table("dim_aerolinea").alias("a")
dim_origen = read_table("dim_origen").alias("o")
dim_destino = read_table("dim_destino").alias("d")


# 2) Reemplazo del SELECT/JOIN que antes venía desde Azure SQL JDBC
#    Se asumen los mismos nombres de columnas que usabas en Azure:
#    f.dim_hora_id, f.dim_hora_arr_id, f.dim_fecha_id, f.dim_aerolinea_id,
#    f.dim_origen_id, f.dim_destino_id, dep.hhmm, arr.hhmm, etc.
df = (
    fact
    .join(broadcast(dim_hora_dep), col("f.dim_hora_id") == col("dep.dim_hora_id"), "inner")
    .join(broadcast(dim_hora_arr), col("f.dim_hora_arr_id") == col("arr.dim_hora_id"), "inner")
    .join(broadcast(dim_fecha), col("f.dim_fecha_id") == col("fe.dim_fecha_id"), "inner")
    .join(broadcast(dim_aerolinea), col("f.dim_aerolinea_id") == col("a.dim_aerolinea_id"), "inner")
    .join(broadcast(dim_origen), col("f.dim_origen_id") == col("o.dim_origen_id"), "inner")
    .join(broadcast(dim_destino), col("f.dim_destino_id") == col("d.dim_destino_id"), "inner")
    .select(
        col("dep.hhmm").alias("CRSDepTime"),
        col("arr.hhmm").alias("CRSArrTime"),
        col("f.Distance").alias("Distance"),
        col("fe.DayOfWeek").alias("DayOfWeek"),
        col("fe.Month").alias("Month"),
        col("fe.Year").alias("Year"),
        col("a.Airline").alias("Airline"),
        col("o.Origin").alias("Origin"),
        col("d.Dest").alias("Dest"),
        col("f.DepTimeBlk").alias("DepTimeBlk"),
        col("f.ArrTimeBlk").alias("ArrTimeBlk"),
        col("f.DepDel15").alias("DepDel15"),
    )
)

ml_columns = [
    "CRSDepTime", "CRSArrTime", "Distance", "DayOfWeek", "Month", "Year",
    "Airline", "Origin", "Dest", "DepTimeBlk", "ArrTimeBlk", "DepDel15"
]

df_ml = (
    df.select(ml_columns)
      .dropna(subset=["DepDel15", "Year"])
      .withColumn("CRSDepTime", col("CRSDepTime").cast("int"))
      .withColumn("CRSArrTime", col("CRSArrTime").cast("int"))
      .withColumn("Distance", col("Distance").cast("double"))
      .withColumn("DayOfWeek", col("DayOfWeek").cast("int"))
      .withColumn("Month", col("Month").cast("int"))
      .withColumn("Year", col("Year").cast("int"))
      .withColumn("DepHour", (col("CRSDepTime") / 100).cast("int"))
      .withColumn("ArrHour", (col("CRSArrTime") / 100).cast("int"))
      .withColumn("label", col("DepDel15").cast("double"))
      .dropna(subset=["Distance", "DayOfWeek", "Month", "Year", "DepHour", "ArrHour", "label"])
)


# 3) Validación temporal + reducción de cardinalidad sin fuga de información
#    Entrena con años anteriores y valida con el año más reciente.

def top_categories(input_df, col_name, top_n):
    return (
        input_df.groupBy(col_name)
        .count()
        .orderBy(desc("count"))
        .limit(top_n)
        .select(col_name)
    )


def replace_other(input_df, col_name, top_df):
    keep_df = broadcast(top_df.withColumnRenamed(col_name, f"{col_name}_keep"))
    return (
        input_df
        .join(keep_df, input_df[col_name] == col(f"{col_name}_keep"), "left")
        .withColumn(
            col_name,
            when(col(f"{col_name}_keep").isNull(), "OTHER").otherwise(col(col_name))
        )
        .drop(f"{col_name}_keep")
    )


df_ml = df_ml.repartition(8).cache()
total_rows = df_ml.count()
print(f"Dataset ML: {total_rows:,} rows")

max_year = df_ml.agg({"Year": "max"}).collect()[0][0]
train_df = df_ml.filter(col("Year") < max_year)
test_df = df_ml.filter(col("Year") == max_year)

print(f"Año más reciente usado para validación temporal: {max_year}")
print(f"Train temporal (< {max_year}): {train_df.count():,} rows")
print(f"Validación temporal (= {max_year}): {test_df.count():,} rows")

# Top categorías calculadas SOLO con entrenamiento para no mirar el año de validación.
for col_name, top_n in [
    ("Airline", 10),
    ("Origin", 20),
    ("Dest", 20),
    ("DepTimeBlk", 12),
    ("ArrTimeBlk", 12),
]:
    top_df = top_categories(train_df, col_name, top_n)
    train_df = replace_other(train_df, col_name, top_df)
    test_df = replace_other(test_df, col_name, top_df)

train_df = train_df.cache()
test_df = test_df.cache()

print("Distribución de clase en entrenamiento:")
train_df.groupBy("label").count().orderBy("label").show()

print("Distribución de clase en validación temporal:")
test_df.groupBy("label").count().orderBy("label").show()


# 4) Pipeline Spark ML
categorical_cols = ["Airline", "Origin", "Dest", "DepTimeBlk", "ArrTimeBlk"]

indexers = [
    StringIndexer(inputCol=c, outputCol=f"{c}_idx", handleInvalid="keep")
    for c in categorical_cols
]

feature_cols = [
    "Distance", "DayOfWeek", "Month", "DepHour", "ArrHour"
] + [f"{c}_idx" for c in categorical_cols]

assembler = VectorAssembler(
    inputCols=feature_cols,
    outputCol="features",
    handleInvalid="keep"
)

lr = LogisticRegression(featuresCol="features", labelCol="label", maxIter=30)

rf = RandomForestClassifier(
    featuresCol="features",
    labelCol="label",
    numTrees=20,
    maxDepth=10,
    seed=42
)

# Métricas principales por desbalance: AUC-ROC y F1-Score.
evaluator_auc = BinaryClassificationEvaluator(
    labelCol="label",
    rawPredictionCol="rawPrediction",
    metricName="areaUnderROC"
)

evaluator_f1 = MulticlassClassificationEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="f1"
)

# Accuracy queda solo como referencia secundaria.
evaluator_acc = MulticlassClassificationEvaluator(
    labelCol="label",
    predictionCol="prediction",
    metricName="accuracy"
)


def print_metrics(name, pred):
    print(f"{name} AUC-ROC:", evaluator_auc.evaluate(pred))
    print(f"{name} F1-Score:", evaluator_f1.evaluate(pred))
    print(f"{name} Accuracy referencia:", evaluator_acc.evaluate(pred))
    print(f"Matriz de confusión {name}:")
    pred.groupBy("label", "prediction").count().orderBy("label", "prediction").show()


# Logistic Regression
lr_pipeline = Pipeline(stages=indexers + [assembler, lr])
lr_model = lr_pipeline.fit(train_df)
lr_pred = lr_model.transform(test_df)

print_metrics("LR", lr_pred)


# Random Forest
rf_pipeline = Pipeline(stages=indexers + [assembler, rf])
rf_model = rf_pipeline.fit(train_df)
rf_pred = rf_model.transform(test_df)

print_metrics("RF_20trees", rf_pred)


# 5) Guardar modelo Random Forest de 20 árboles en HDFS
rf_model.write().overwrite().save(MODEL_OUT)
print(f"Modelo guardado en: {MODEL_OUT}")

spark.stop()
