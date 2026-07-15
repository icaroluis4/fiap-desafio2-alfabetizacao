"""Carrega CSVs do GCS para tabelas BigQuery na camada Bronze."""
from __future__ import annotations

import sys
from pathlib import Path

from google.cloud import bigquery

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    GCP_PROJECT_ID,
    GCS_BUCKET_NAME,
    BQ_DATASET_BRONZE,
)


def carregar_csv_para_bq(
    gcs_uri: str,
    table_id: str,
    dataset_id: str = BQ_DATASET_BRONZE,
    project_id: str = GCP_PROJECT_ID,
    skip_leading_rows: int = 1,
    encoding: str = "UTF-8",
    delimiter: str = ",",
) -> None:
    """Carrega um arquivo CSV do GCS para uma tabela BigQuery.

    Args:
        gcs_uri: URI gs:// do arquivo.
        table_id: Nome da tabela de destino.
        dataset_id: Dataset de destino.
        project_id: ID do projeto GCP.
        skip_leading_rows: Linhas a pular no início (header).
        encoding: Encoding do arquivo.
        delimiter: Delimitador de campos.
    """
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=skip_leading_rows,
        autodetect=True,
        encoding=encoding,
        field_delimiter=delimiter,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    print(f"  Carregando {gcs_uri} → {table_ref} ...")
    load_job = client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)
    load_job.result()  # Aguarda conclusão

    table = client.get_table(table_ref)
    print(f"  ✓ {table.num_rows:,} linhas carregadas em {table_ref}")


def main() -> None:
    """Carrega todas as fontes de dados da camada Bronze."""
    bucket = f"gs://{GCS_BUCKET_NAME}"

    # Configurações de fontes: (prefixo, tabela, encoding, delimiter, skip_rows)
    fontes = [
        # Metas e Resultados
        (f"{bucket}/metas_resultados/resultados_e_metas_municipios_2025_v2_Divulga_o_Alfabet_Municipio.csv",
         "metas_municipios", "UTF-8", ",", 1),
        (f"{bucket}/metas_resultados/resultados_e_metas_municipios_2025_v2_Vari_veis.csv",
         "metas_municipios_variaveis", "UTF-8", ",", 1),
        (f"{bucket}/metas_resultados/resultados_e_metas_ufs_2025_v1_Divulga_o_Alfabet_UF_e_Brasil.csv",
         "metas_ufs", "UTF-8", ",", 1),
        (f"{bucket}/metas_resultados/resultados_e_metas_ufs_2025_v1_vari_veis.csv",
         "metas_ufs_variaveis", "UTF-8", ",", 1),

        # AEEB 2025
        (f"{bucket}/aeeb2025/TS_ALUNO.csv",
         "aeeb_ts_aluno", "ISO-8859-1", ";", 1),
        (f"{bucket}/aeeb2025/TS_ESTADO.csv",
         "aeeb_ts_estado", "ISO-8859-1", ";", 1),
        (f"{bucket}/aeeb2025/TS_ITEM.csv",
         "aeeb_ts_item", "ISO-8859-1", ";", 1),
        (f"{bucket}/aeeb2025/TS_MUNICIPIO.csv",
         "aeeb_ts_municipio", "ISO-8859-1", ";", 1),

        # Censo 2024
        (f"{bucket}/censo2024/microdados_ed_basica_2024.csv",
         "censo_escola", "ISO-8859-1", ";", 1),
        (f"{bucket}/censo2024/suplemento_cursos_tecnicos_2024.csv",
         "censo_suplemento_tecnico", "ISO-8859-1", ";", 1),
    ]

    for gcs_uri, table_id, encoding, delimiter, skip_rows in fontes:
        try:
            carregar_csv_para_bq(
                gcs_uri=gcs_uri,
                table_id=table_id,
                encoding=encoding,
                delimiter=delimiter,
                skip_leading_rows=skip_rows,
            )
        except Exception as exc:
            print(f"  ✗ Erro ao carregar {table_id}: {exc}")

    print("\n✅ Carga da camada Bronze concluída.")


if __name__ == "__main__":
    main()
