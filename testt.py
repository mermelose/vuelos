from pathlib import Path
import pandas as pd


BASE_PATH = Path("datamart")
FACT_PATH = BASE_PATH / "dim_fecha"
OUTPUT_PATH = Path("dim_fecha.csv")


def main():
    parquet_files = list(FACT_PATH.glob("*.parquet"))

    if not parquet_files:
        raise FileNotFoundError(f"No se encontraron archivos .parquet en {FACT_PATH}")

    print(f"Archivos encontrados: {len(parquet_files)}")

    dfs = []
    for file in parquet_files:
        print(f"Leyendo: {file}")
        df = pd.read_parquet(file)
        dfs.append(df)

    fact = pd.concat(dfs, ignore_index=True)

    print(f"Filas totales: {len(fact):,}")
    print(f"Columnas: {len(fact.columns)}")
    print("Exportando a CSV...")

    fact.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"CSV creado correctamente: {OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()