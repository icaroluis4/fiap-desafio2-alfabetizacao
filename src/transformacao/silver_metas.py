"""Transforma dados de Metas e Resultados da Bronze para Silver.

Limpeza aplicada:
- Remove header duplicado (linha 0 da Bronze = nomes técnicos)
- Renomeia colunas para snake_case padronizado
- Converte percentuais e códigos para tipos numéricos
- Remove linhas de totalizador ou em branco
"""
from __future__ import annotations

import sys
from pathlib import Path

from google.cloud import bigquery

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import GCP_PROJECT_ID, BQ_DATASET_BRONZE, BQ_DATASET_SILVER


def transformar_metas_municipios() -> None:
    """Cria tabela silver a partir de bronze_alfabetizacao.metas_municipios."""
    client = bigquery.Client(project=GCP_PROJECT_ID)

    query = f"""
    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.metas_municipios` AS
    SELECT
      SAFE_CAST(string_field_1 AS INT64) AS co_uf,
      string_field_2 AS sg_uf,
      SAFE_CAST(string_field_3 AS INT64) AS co_municipio,
      string_field_4 AS no_municipio,
      string_field_5 AS tp_rede,
      SAFE_CAST(REPLACE(string_field_6, ',', '.') AS FLOAT64) AS pc_alfabetizado_2023,
      SAFE_CAST(REPLACE(string_field_7, ',', '.') AS FLOAT64) AS pc_alfabetizado_2024,
      SAFE_CAST(REPLACE(string_field_8, ',', '.') AS FLOAT64) AS pc_alfabetizado_2025,
      SAFE_CAST(REPLACE(string_field_9, ',', '.') AS FLOAT64) AS meta_2024,
      SAFE_CAST(REPLACE(string_field_10, ',', '.') AS FLOAT64) AS meta_2025,
      SAFE_CAST(REPLACE(string_field_11, ',', '.') AS FLOAT64) AS meta_2026,
      SAFE_CAST(REPLACE(string_field_12, ',', '.') AS FLOAT64) AS meta_2027,
      SAFE_CAST(REPLACE(string_field_13, ',', '.') AS FLOAT64) AS meta_2028,
      SAFE_CAST(REPLACE(string_field_14, ',', '.') AS FLOAT64) AS meta_2029,
      SAFE_CAST(REPLACE(string_field_15, ',', '.') AS FLOAT64) AS meta_2030,
      SAFE_CAST(string_field_16 AS INT64) AS co_nivel_alfabetizacao,
      SAFE_CAST(REPLACE(string_field_17, ',', '.') AS FLOAT64) AS pc_participacao
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_BRONZE}.metas_municipios`
    WHERE string_field_0 != 'ANO'
      AND string_field_3 IS NOT NULL
      AND string_field_3 != ''
    """

    job = client.query(query)
    job.result()
    print("✓ silver.metas_municipios criada")


def transformar_metas_ufs() -> None:
    """Cria tabela silver a partir de bronze_alfabetizacao.metas_ufs."""
    client = bigquery.Client(project=GCP_PROJECT_ID)

    query = f"""
    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.metas_ufs` AS
    SELECT
      SAFE_CAST(string_field_1 AS INT64) AS co_uf,
      string_field_2 AS sg_uf,
      string_field_3 AS no_uf,
      string_field_4 AS tp_rede,
      SAFE_CAST(REPLACE(string_field_5, ',', '.') AS FLOAT64) AS pc_alfabetizado_2023,
      SAFE_CAST(REPLACE(string_field_6, ',', '.') AS FLOAT64) AS pc_alfabetizado_2024,
      SAFE_CAST(REPLACE(string_field_7, ',', '.') AS FLOAT64) AS pc_alfabetizado_2025,
      SAFE_CAST(REPLACE(string_field_8, ',', '.') AS FLOAT64) AS meta_2024,
      SAFE_CAST(REPLACE(string_field_9, ',', '.') AS FLOAT64) AS meta_2025,
      SAFE_CAST(REPLACE(string_field_10, ',', '.') AS FLOAT64) AS meta_2026,
      SAFE_CAST(REPLACE(string_field_11, ',', '.') AS FLOAT64) AS meta_2027,
      SAFE_CAST(REPLACE(string_field_12, ',', '.') AS FLOAT64) AS meta_2028,
      SAFE_CAST(REPLACE(string_field_13, ',', '.') AS FLOAT64) AS meta_2029,
      SAFE_CAST(REPLACE(string_field_14, ',', '.') AS FLOAT64) AS meta_2030,
      string_field_15 AS ds_nivel_alfabetizacao
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_BRONZE}.metas_ufs`
    WHERE string_field_0 != 'ANO'
      AND string_field_1 IS NOT NULL
      AND string_field_1 != ''
      AND string_field_1 != 'CÓDIGO UF'
    """

    job = client.query(query)
    job.result()
    print("✓ silver.metas_ufs criada")


def main() -> None:
    print("Transformando Metas e Resultados → Silver...")
    transformar_metas_municipios()
    transformar_metas_ufs()
    print("\n✅ Camada Silver — Metas concluída.")


if __name__ == "__main__":
    main()
