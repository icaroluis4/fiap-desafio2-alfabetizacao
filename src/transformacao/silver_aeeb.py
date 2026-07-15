"""Transforma microdados AEEB 2025 da Bronze para Silver.

Limpeza aplicada:
- Renomeia colunas para snake_case
- Converte códigos e percentuais para tipos numéricos
- Mantém apenas colunas analíticas relevantes (remove respostas brutas de blocos)
"""
from __future__ import annotations

import sys
from pathlib import Path

from google.cloud import bigquery

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import GCP_PROJECT_ID, BQ_DATASET_BRONZE, BQ_DATASET_SILVER


def transformar_aeeb_municipio() -> None:
    """Cria tabela silver a partir de aeeb_ts_municipio."""
    client = bigquery.Client(project=GCP_PROJECT_ID)

    query = f"""
    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.aeeb_municipio` AS
    SELECT
      SAFE_CAST(NU_ANO_AVALIACAO AS INT64) AS nu_ano_avaliacao,
      SAFE_CAST(CO_UF AS INT64) AS co_uf,
      SG_UF,
      SAFE_CAST(CO_MUNICIPIO AS INT64) AS co_municipio,
      NO_MUNICIPIO,
      SAFE_CAST(TP_SERIE AS INT64) AS tp_serie,
      SAFE_CAST(ID_TIPO_REDE AS INT64) AS id_tipo_rede,
      PC_ALUNO_ALFABETIZADO AS pc_aluno_alfabetizado,
      VL_MEDIA_LP AS vl_media_lp,
      PC_ALUNO_NIVEL_0_LP AS pc_nivel_0,
      PC_ALUNO_NIVEL_1_LP AS pc_nivel_1,
      PC_ALUNO_NIVEL_2_LP AS pc_nivel_2,
      PC_ALUNO_NIVEL_3_LP AS pc_nivel_3,
      PC_ALUNO_NIVEL_4_LP AS pc_nivel_4,
      PC_ALUNO_NIVEL_5_LP AS pc_nivel_5,
      PC_ALUNO_NIVEL_6_LP AS pc_nivel_6,
      PC_ALUNO_NIVEL_7_LP AS pc_nivel_7,
      PC_ALUNO_NIVEL_8_LP AS pc_nivel_8
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_BRONZE}.aeeb_ts_municipio`
    WHERE CO_MUNICIPIO IS NOT NULL
    """

    job = client.query(query)
    job.result()
    print("✓ silver.aeeb_municipio criada")


def transformar_aeeb_estado() -> None:
    """Cria tabela silver a partir de aeeb_ts_estado."""
    client = bigquery.Client(project=GCP_PROJECT_ID)

    query = f"""
    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.aeeb_estado` AS
    SELECT
      SAFE_CAST(NU_ANO_AVALIACAO AS INT64) AS nu_ano_avaliacao,
      SAFE_CAST(CO_UF AS INT64) AS co_uf,
      SG_UF,
      SAFE_CAST(TP_SERIE AS INT64) AS tp_serie,
      SAFE_CAST(ID_TIPO_REDE AS INT64) AS id_tipo_rede,
      PC_ALUNO_ALFABETIZADO AS pc_aluno_alfabetizado,
      VL_MEDIA_LP AS vl_media_lp,
      PC_ALUNO_NIVEL_0_LP AS pc_nivel_0,
      PC_ALUNO_NIVEL_1_LP AS pc_nivel_1,
      PC_ALUNO_NIVEL_2_LP AS pc_nivel_2,
      PC_ALUNO_NIVEL_3_LP AS pc_nivel_3,
      PC_ALUNO_NIVEL_4_LP AS pc_nivel_4,
      PC_ALUNO_NIVEL_5_LP AS pc_nivel_5,
      PC_ALUNO_NIVEL_6_LP AS pc_nivel_6,
      PC_ALUNO_NIVEL_7_LP AS pc_nivel_7,
      PC_ALUNO_NIVEL_8_LP AS pc_nivel_8
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_BRONZE}.aeeb_ts_estado`
    WHERE CO_UF IS NOT NULL
    """

    job = client.query(query)
    job.result()
    print("✓ silver.aeeb_estado criada")


def main() -> None:
    print("Transformando AEEB 2025 → Silver...")
    transformar_aeeb_municipio()
    transformar_aeeb_estado()
    print("\n✅ Camada Silver — AEEB concluída.")


if __name__ == "__main__":
    main()
