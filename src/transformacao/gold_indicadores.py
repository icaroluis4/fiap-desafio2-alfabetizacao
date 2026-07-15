"""Constrói a camada Gold — indicadores analíticos de alfabetização.

Tabelas geradas:
1. indicador_municipio  — AEEB + Metas + Censo agregados por município
2. metas_vs_resultados  — gap entre meta e resultado (município e UF)
3. indicador_uf         — visão estadual consolidada

Decisões de join:
- AEEB id_tipo_rede = 3 (Municipal) ↔ Metas tp_rede = 'MUNICIPAL'
- Censo agregado por co_municipio (escolas com anos iniciais do fundamental)
"""
from __future__ import annotations

import sys
from pathlib import Path

from google.cloud import bigquery

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import GCP_PROJECT_ID, BQ_DATASET_SILVER, BQ_DATASET_GOLD


def criar_indicador_municipio() -> None:
    """Integra AEEB + Metas + Censo em uma tabela analítica por município."""
    client = bigquery.Client(project=GCP_PROJECT_ID)

    query = f"""
    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.indicador_municipio` AS
    WITH
    -- AEEB: rede municipal (id_tipo_rede = 3)
    aeeb AS (
      SELECT
        co_uf,
        SG_UF AS sg_uf,
        co_municipio,
        NO_MUNICIPIO AS no_municipio,
        nu_ano_avaliacao,
        pc_aluno_alfabetizado,
        vl_media_lp,
        pc_nivel_0,
        pc_nivel_1,
        pc_nivel_2,
        pc_nivel_3,
        pc_nivel_4,
        pc_nivel_5,
        pc_nivel_6,
        pc_nivel_7,
        pc_nivel_8
      FROM `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.aeeb_municipio`
      WHERE id_tipo_rede = 3
        AND co_municipio IS NOT NULL
    ),

    -- Metas: rede municipal
    metas AS (
      SELECT
        co_municipio,
        pc_alfabetizado_2023,
        pc_alfabetizado_2024,
        pc_alfabetizado_2025,
        meta_2024,
        meta_2025,
        meta_2026,
        meta_2027,
        meta_2028,
        meta_2029,
        meta_2030,
        co_nivel_alfabetizacao,
        pc_participacao
      FROM `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.metas_municipios`
      WHERE tp_rede = 'MUNICIPAL'
        AND co_municipio IS NOT NULL
    ),

    -- Censo: agregação municipal (escolas com anos iniciais)
    censo AS (
      SELECT
        co_municipio,
        COUNT(DISTINCT co_entidade) AS qtd_escolas,
        COUNTIF(tp_dependencia = 3) AS qtd_escolas_municipais,
        COUNTIF(tp_dependencia = 2) AS qtd_escolas_estaduais,
        COUNTIF(tp_dependencia = 4) AS qtd_escolas_privadas,
        COUNTIF(tp_localizacao = 1) AS qtd_escolas_urbanas,
        COUNTIF(tp_localizacao = 2) AS qtd_escolas_rurais,
        SUM(IFNULL(qt_mat_fund_ai, 0)) AS total_mat_fund_ai,
        SUM(IFNULL(qt_mat_fund_ai_1, 0) + IFNULL(qt_mat_fund_ai_2, 0)) AS total_mat_1_2_ano,
        SUM(IFNULL(qt_doc_fund_ai, 0)) AS total_doc_fund_ai,
        SUM(IFNULL(qt_tur_fund_ai, 0)) AS total_tur_fund_ai,
        ROUND(AVG(IFNULL(in_internet, 0)), 4) AS pct_escolas_com_internet,
        ROUND(AVG(IFNULL(in_biblioteca, 0)), 4) AS pct_escolas_com_biblioteca,
        ROUND(AVG(IFNULL(in_lab_informatica, 0)), 4) AS pct_escolas_com_lab_info,
        ROUND(AVG(IFNULL(in_agua_potavel, 0)), 4) AS pct_escolas_agua_potavel,
        ROUND(AVG(IFNULL(in_energia_rede_publica, 0)), 4) AS pct_escolas_energia
      FROM `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.censo_escola`
      WHERE co_municipio IS NOT NULL
        AND (
          IFNULL(in_fund_ai, 0) = 1
          OR IFNULL(qt_mat_fund_ai, 0) > 0
        )
      GROUP BY co_municipio
    )

    SELECT
      a.co_uf,
      a.sg_uf,
      a.co_municipio,
      a.no_municipio,
      a.nu_ano_avaliacao,

      -- Resultado AEEB 2025
      a.pc_aluno_alfabetizado AS pc_alfabetizado_aeeb_2025,
      a.vl_media_lp,
      a.pc_nivel_0,
      a.pc_nivel_1,
      a.pc_nivel_2,
      a.pc_nivel_3,
      a.pc_nivel_4,
      a.pc_nivel_5,
      a.pc_nivel_6,
      a.pc_nivel_7,
      a.pc_nivel_8,

      -- Série histórica e metas (fonte Metas/Resultados)
      m.pc_alfabetizado_2023,
      m.pc_alfabetizado_2024,
      m.pc_alfabetizado_2025 AS pc_alfabetizado_metas_2025,
      m.meta_2024,
      m.meta_2025,
      m.meta_2026,
      m.meta_2027,
      m.meta_2028,
      m.meta_2029,
      m.meta_2030,
      m.co_nivel_alfabetizacao,
      m.pc_participacao,

      -- Gap meta vs resultado 2025
      ROUND(m.pc_alfabetizado_2025 - m.meta_2025, 2) AS gap_meta_2025,
      CASE
        WHEN m.meta_2025 IS NULL OR m.pc_alfabetizado_2025 IS NULL THEN NULL
        WHEN m.pc_alfabetizado_2025 >= m.meta_2025 THEN TRUE
        ELSE FALSE
      END AS atingiu_meta_2025,

      -- Evolução 2023 → 2025
      ROUND(m.pc_alfabetizado_2025 - m.pc_alfabetizado_2023, 2) AS evolucao_2023_2025,

      -- Contexto escolar (Censo 2024)
      c.qtd_escolas,
      c.qtd_escolas_municipais,
      c.qtd_escolas_estaduais,
      c.qtd_escolas_privadas,
      c.qtd_escolas_urbanas,
      c.qtd_escolas_rurais,
      c.total_mat_fund_ai,
      c.total_mat_1_2_ano,
      c.total_doc_fund_ai,
      c.total_tur_fund_ai,
      c.pct_escolas_com_internet,
      c.pct_escolas_com_biblioteca,
      c.pct_escolas_com_lab_info,
      c.pct_escolas_agua_potavel,
      c.pct_escolas_energia,

      -- Densidade docente (alunos por docente nos anos iniciais)
      CASE
        WHEN c.total_doc_fund_ai > 0
        THEN ROUND(c.total_mat_fund_ai / c.total_doc_fund_ai, 2)
        ELSE NULL
      END AS alunos_por_docente_ai

    FROM aeeb a
    LEFT JOIN metas m ON a.co_municipio = m.co_municipio
    LEFT JOIN censo c ON a.co_municipio = c.co_municipio
    """

    job = client.query(query)
    job.result()

    count = list(client.query(
        f"SELECT COUNT(*) AS n FROM `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.indicador_municipio`"
    ).result())[0].n
    print(f"✓ gold.indicador_municipio criada ({count:,} linhas)")


def criar_metas_vs_resultados() -> None:
    """Tabela de gap análise: meta vs resultado por município e por UF."""
    client = bigquery.Client(project=GCP_PROJECT_ID)

    query = f"""
    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.metas_vs_resultados` AS

    -- Nível município
    SELECT
      'municipio' AS nivel,
      CAST(co_municipio AS STRING) AS codigo,
      no_municipio AS nome,
      sg_uf,
      co_uf,
      pc_alfabetizado_2023,
      pc_alfabetizado_2024,
      pc_alfabetizado_metas_2025 AS pc_alfabetizado_2025,
      meta_2024,
      meta_2025,
      meta_2026,
      meta_2030,
      gap_meta_2025,
      atingiu_meta_2025,
      evolucao_2023_2025,
      pc_participacao,
      co_nivel_alfabetizacao
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.indicador_municipio`
    WHERE meta_2025 IS NOT NULL

    UNION ALL

    -- Nível UF
    SELECT
      'uf' AS nivel,
      CAST(m.co_uf AS STRING) AS codigo,
      m.no_uf AS nome,
      m.sg_uf,
      m.co_uf,
      m.pc_alfabetizado_2023,
      m.pc_alfabetizado_2024,
      m.pc_alfabetizado_2025,
      m.meta_2024,
      m.meta_2025,
      m.meta_2026,
      m.meta_2030,
      ROUND(m.pc_alfabetizado_2025 - m.meta_2025, 2) AS gap_meta_2025,
      CASE
        WHEN m.meta_2025 IS NULL OR m.pc_alfabetizado_2025 IS NULL THEN NULL
        WHEN m.pc_alfabetizado_2025 >= m.meta_2025 THEN TRUE
        ELSE FALSE
      END AS atingiu_meta_2025,
      ROUND(m.pc_alfabetizado_2025 - m.pc_alfabetizado_2023, 2) AS evolucao_2023_2025,
      CAST(NULL AS FLOAT64) AS pc_participacao,
      SAFE_CAST(m.ds_nivel_alfabetizacao AS INT64) AS co_nivel_alfabetizacao
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.metas_ufs` m
    WHERE m.tp_rede = 'PÚBLICA'
       OR m.tp_rede IS NOT NULL
    """

    job = client.query(query)
    job.result()

    count = list(client.query(
        f"SELECT COUNT(*) AS n FROM `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.metas_vs_resultados`"
    ).result())[0].n
    print(f"✓ gold.metas_vs_resultados criada ({count:,} linhas)")


def criar_indicador_uf() -> None:
    """Consolida indicadores por UF a partir do AEEB estado + Metas UF + Censo."""
    client = bigquery.Client(project=GCP_PROJECT_ID)

    query = f"""
    CREATE OR REPLACE TABLE `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.indicador_uf` AS
    WITH
    aeeb AS (
      SELECT
        co_uf,
        SG_UF AS sg_uf,
        nu_ano_avaliacao,
        pc_aluno_alfabetizado,
        vl_media_lp,
        pc_nivel_0,
        pc_nivel_1,
        pc_nivel_2,
        pc_nivel_3,
        pc_nivel_4,
        pc_nivel_5,
        pc_nivel_6,
        pc_nivel_7,
        pc_nivel_8
      FROM `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.aeeb_estado`
      WHERE id_tipo_rede = 5  -- rede pública consolidada
    ),

    metas AS (
      SELECT
        co_uf,
        no_uf,
        pc_alfabetizado_2023,
        pc_alfabetizado_2024,
        pc_alfabetizado_2025,
        meta_2024,
        meta_2025,
        meta_2026,
        meta_2027,
        meta_2028,
        meta_2029,
        meta_2030,
        ds_nivel_alfabetizacao
      FROM `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.metas_ufs`
      WHERE UPPER(tp_rede) LIKE '%P%BLICA%'
         OR tp_rede = 'PÚBLICA'
    ),

    -- Fallback: se não houver linha PÚBLICA, pega a primeira por UF
    metas_fallback AS (
      SELECT * EXCEPT(rn)
      FROM (
        SELECT
          *,
          ROW_NUMBER() OVER (PARTITION BY co_uf ORDER BY tp_rede) AS rn
        FROM `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.metas_ufs`
      )
      WHERE rn = 1
    ),

    metas_final AS (
      SELECT
        COALESCE(m.co_uf, f.co_uf) AS co_uf,
        COALESCE(m.no_uf, f.no_uf) AS no_uf,
        COALESCE(m.pc_alfabetizado_2023, f.pc_alfabetizado_2023) AS pc_alfabetizado_2023,
        COALESCE(m.pc_alfabetizado_2024, f.pc_alfabetizado_2024) AS pc_alfabetizado_2024,
        COALESCE(m.pc_alfabetizado_2025, f.pc_alfabetizado_2025) AS pc_alfabetizado_2025,
        COALESCE(m.meta_2024, f.meta_2024) AS meta_2024,
        COALESCE(m.meta_2025, f.meta_2025) AS meta_2025,
        COALESCE(m.meta_2026, f.meta_2026) AS meta_2026,
        COALESCE(m.meta_2027, f.meta_2027) AS meta_2027,
        COALESCE(m.meta_2028, f.meta_2028) AS meta_2028,
        COALESCE(m.meta_2029, f.meta_2029) AS meta_2029,
        COALESCE(m.meta_2030, f.meta_2030) AS meta_2030,
        COALESCE(m.ds_nivel_alfabetizacao, f.ds_nivel_alfabetizacao) AS ds_nivel_alfabetizacao
      FROM metas m
      FULL OUTER JOIN metas_fallback f ON m.co_uf = f.co_uf
    ),

    censo AS (
      SELECT
        co_uf,
        COUNT(DISTINCT co_entidade) AS qtd_escolas,
        COUNTIF(tp_dependencia = 3) AS qtd_escolas_municipais,
        SUM(IFNULL(qt_mat_fund_ai, 0)) AS total_mat_fund_ai,
        SUM(IFNULL(qt_doc_fund_ai, 0)) AS total_doc_fund_ai,
        ROUND(AVG(IFNULL(in_internet, 0)), 4) AS pct_escolas_com_internet,
        ROUND(AVG(IFNULL(in_biblioteca, 0)), 4) AS pct_escolas_com_biblioteca
      FROM `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.censo_escola`
      WHERE co_uf IS NOT NULL
        AND (
          IFNULL(in_fund_ai, 0) = 1
          OR IFNULL(qt_mat_fund_ai, 0) > 0
        )
      GROUP BY co_uf
    ),

    -- Contagem de municípios que atingiram a meta (a partir da Gold municipal)
    mun_stats AS (
      SELECT
        co_uf,
        COUNT(*) AS qtd_municipios,
        COUNTIF(atingiu_meta_2025) AS qtd_municipios_atingiram_meta,
        ROUND(AVG(pc_alfabetizado_aeeb_2025), 2) AS media_pc_alfabetizado_mun,
        ROUND(AVG(gap_meta_2025), 2) AS media_gap_meta
      FROM `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.indicador_municipio`
      GROUP BY co_uf
    )

    SELECT
      a.co_uf,
      a.sg_uf,
      mf.no_uf,
      a.nu_ano_avaliacao,

      a.pc_aluno_alfabetizado AS pc_alfabetizado_aeeb_2025,
      a.vl_media_lp,
      a.pc_nivel_0,
      a.pc_nivel_1,
      a.pc_nivel_2,
      a.pc_nivel_3,
      a.pc_nivel_4,
      a.pc_nivel_5,
      a.pc_nivel_6,
      a.pc_nivel_7,
      a.pc_nivel_8,

      mf.pc_alfabetizado_2023,
      mf.pc_alfabetizado_2024,
      mf.pc_alfabetizado_2025 AS pc_alfabetizado_metas_2025,
      mf.meta_2024,
      mf.meta_2025,
      mf.meta_2026,
      mf.meta_2027,
      mf.meta_2028,
      mf.meta_2029,
      mf.meta_2030,
      mf.ds_nivel_alfabetizacao,

      ROUND(mf.pc_alfabetizado_2025 - mf.meta_2025, 2) AS gap_meta_2025,
      CASE
        WHEN mf.meta_2025 IS NULL OR mf.pc_alfabetizado_2025 IS NULL THEN NULL
        WHEN mf.pc_alfabetizado_2025 >= mf.meta_2025 THEN TRUE
        ELSE FALSE
      END AS atingiu_meta_2025,
      ROUND(mf.pc_alfabetizado_2025 - mf.pc_alfabetizado_2023, 2) AS evolucao_2023_2025,

      c.qtd_escolas,
      c.qtd_escolas_municipais,
      c.total_mat_fund_ai,
      c.total_doc_fund_ai,
      c.pct_escolas_com_internet,
      c.pct_escolas_com_biblioteca,

      ms.qtd_municipios,
      ms.qtd_municipios_atingiram_meta,
      ROUND(
        SAFE_DIVIDE(ms.qtd_municipios_atingiram_meta, ms.qtd_municipios) * 100, 2
      ) AS pct_municipios_atingiram_meta,
      ms.media_pc_alfabetizado_mun,
      ms.media_gap_meta

    FROM aeeb a
    LEFT JOIN metas_final mf ON a.co_uf = mf.co_uf
    LEFT JOIN censo c ON a.co_uf = c.co_uf
    LEFT JOIN mun_stats ms ON a.co_uf = ms.co_uf
    """

    job = client.query(query)
    job.result()

    count = list(client.query(
        f"SELECT COUNT(*) AS n FROM `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.indicador_uf`"
    ).result())[0].n
    print(f"✓ gold.indicador_uf criada ({count:,} linhas)")


def main() -> None:
    print("Construindo camada Gold — indicadores de alfabetização...\n")
    criar_indicador_municipio()
    criar_metas_vs_resultados()
    criar_indicador_uf()
    print("\n✅ Camada Gold concluída.")


if __name__ == "__main__":
    main()
