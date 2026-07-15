"""Transforma microdados Censo Escolar 2024 da Bronze para Silver.

Seleciona apenas colunas relevantes para enriquecimento da análise de alfabetização:
- Identificação da escola e localização
- Dependência administrativa e tipo de rede
- Quantidade de matrículas e turmas (foco em anos iniciais)
- Infraestrutura básica
"""
from __future__ import annotations

import sys
from pathlib import Path

from google.cloud import bigquery

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import GCP_PROJECT_ID, BQ_DATASET_BRONZE, BQ_DATASET_SILVER


def transformar_censo_escola() -> None:
    """Cria tabela silver com colunas selecionadas do Censo Escolar."""
    client = bigquery.Client(project=GCP_PROJECT_ID)

    query = f"""
    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.censo_escola` AS
    SELECT
      SAFE_CAST(NU_ANO_CENSO AS INT64) AS nu_ano_censo,
      NO_REGIAO,
      SAFE_CAST(CO_REGIAO AS INT64) AS co_regiao,
      NO_UF,
      SG_UF,
      SAFE_CAST(CO_UF AS INT64) AS co_uf,
      NO_MUNICIPIO,
      SAFE_CAST(CO_MUNICIPIO AS INT64) AS co_municipio,
      NO_ENTIDADE,
      SAFE_CAST(CO_ENTIDADE AS INT64) AS co_entidade,

      -- Dependência e rede
      SAFE_CAST(TP_DEPENDENCIA AS INT64) AS tp_dependencia,
      SAFE_CAST(TP_LOCALIZACAO AS INT64) AS tp_localizacao,
      SAFE_CAST(TP_LOCALIZACAO_DIFERENCIADA AS INT64) AS tp_localizacao_diferenciada,
      SAFE_CAST(TP_SITUACAO_FUNCIONAMENTO AS INT64) AS tp_situacao_funcionamento,

      -- Matrículas (foco anos iniciais do fundamental)
      SAFE_CAST(QT_MAT_BAS AS INT64) AS qt_mat_bas,
      SAFE_CAST(QT_MAT_FUND AS INT64) AS qt_mat_fund,
      SAFE_CAST(QT_MAT_FUND_AI AS INT64) AS qt_mat_fund_ai,
      SAFE_CAST(QT_MAT_FUND_AI_1 AS INT64) AS qt_mat_fund_ai_1,
      SAFE_CAST(QT_MAT_FUND_AI_2 AS INT64) AS qt_mat_fund_ai_2,
      SAFE_CAST(QT_MAT_FUND_AI_3 AS INT64) AS qt_mat_fund_ai_3,
      SAFE_CAST(QT_MAT_FUND_AI_4 AS INT64) AS qt_mat_fund_ai_4,
      SAFE_CAST(QT_MAT_FUND_AI_5 AS INT64) AS qt_mat_fund_ai_5,

      -- Turmas
      SAFE_CAST(QT_TUR_BAS AS INT64) AS qt_tur_bas,
      SAFE_CAST(QT_TUR_FUND_AI AS INT64) AS qt_tur_fund_ai,

      -- Docentes
      SAFE_CAST(QT_DOC_BAS AS INT64) AS qt_doc_bas,
      SAFE_CAST(QT_DOC_FUND_AI AS INT64) AS qt_doc_fund_ai,

      -- Infraestrutura básica (flags binárias)
      SAFE_CAST(IN_AGUA_POTAVEL AS INT64) AS in_agua_potavel,
      SAFE_CAST(IN_ENERGIA_REDE_PUBLICA AS INT64) AS in_energia_rede_publica,
      SAFE_CAST(IN_ESGOTO_REDE_PUBLICA AS INT64) AS in_esgoto_rede_publica,
      SAFE_CAST(IN_BANHEIRO AS INT64) AS in_banheiro,
      SAFE_CAST(IN_BIBLIOTECA AS INT64) AS in_biblioteca,
      SAFE_CAST(IN_LABORATORIO_INFORMATICA AS INT64) AS in_lab_informatica,
      SAFE_CAST(IN_INTERNET AS INT64) AS in_internet,
      SAFE_CAST(IN_ALIMENTACAO AS INT64) AS in_alimentacao,

      -- Acessibilidade
      SAFE_CAST(IN_ACESSIBILIDADE_INEXISTENTE AS INT64) AS in_acessibilidade_inexistente,

      -- Modalidades oferecidas
      SAFE_CAST(IN_INF AS INT64) AS in_infantil,
      SAFE_CAST(IN_FUND_AI AS INT64) AS in_fund_ai,
      SAFE_CAST(IN_REGULAR AS INT64) AS in_regular,
      SAFE_CAST(IN_EJA AS INT64) AS in_eja

    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_BRONZE}.censo_escola`
    WHERE CO_ENTIDADE IS NOT NULL
    """

    job = client.query(query)
    job.result()
    print("✓ silver.censo_escola criada")


def main() -> None:
    print("Transformando Censo Escolar 2024 → Silver...")
    transformar_censo_escola()
    print("\n✅ Camada Silver — Censo concluída.")


if __name__ == "__main__":
    main()
