"""Sobe arquivos CSV locais para o Google Cloud Storage (camada Bronze)."""
from __future__ import annotations

import sys
from pathlib import Path

from google.cloud import storage

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import GCP_PROJECT_ID, GCS_BUCKET_NAME, LOCAL_DATA_PATH, MICRODADOS_AEEB_PATH, MICRODADOS_CENSO_PATH


def upload_arquivo(
    local_path: Path,
    bucket_name: str = GCS_BUCKET_NAME,
    project_id: str = GCP_PROJECT_ID,
    destino_prefixo: str = "",
) -> str:
    """Faz upload de um arquivo local para o GCS.

    Args:
        local_path: Caminho do arquivo local.
        bucket_name: Nome do bucket GCS.
        project_id: ID do projeto GCP.
        destino_prefixo: Prefixo no bucket (ex: 'aeeb2025/').

    Returns:
        URI gs:// do arquivo enviado.
    """
    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)

    blob_name = f"{destino_prefixo}{local_path.name}" if destino_prefixo else local_path.name
    blob = bucket.blob(blob_name)

    blob.upload_from_filename(str(local_path))
    uri = f"gs://{bucket_name}/{blob_name}"
    print(f"  ✓ {local_path.name} → {uri}")
    return uri


def upload_pasta(
    pasta_local: Path,
    prefixo: str,
    bucket_name: str = GCS_BUCKET_NAME,
    project_id: str = GCP_PROJECT_ID,
    padrao: str = "*.csv",
) -> list[str]:
    """Faz upload de todos os arquivos CSV de uma pasta para o GCS.

    Args:
        pasta_local: Pasta com os arquivos.
        prefixo: Prefixo no bucket.
        bucket_name: Nome do bucket.
        project_id: ID do projeto.
        padrao: Padrão de arquivo (default: *.csv).

    Returns:
        Lista de URIs enviados.
    """
    arquivos = sorted(pasta_local.glob(padrao))
    if not arquivos:
        print(f"  ⚠ Nenhum arquivo encontrado em {pasta_local}")
        return []

    uris = []
    for arquivo in arquivos:
        uri = upload_arquivo(arquivo, bucket_name, project_id, prefixo)
        uris.append(uri)
    return uris


def main() -> None:
    """Executa o upload de todas as fontes de dados para o GCS."""
    print(f"Bucket destino: gs://{GCS_BUCKET_NAME}\n")

    # 1. Metas e Resultados (convertidos de Excel)
    print("📁 Upload: Metas e Resultados")
    upload_pasta(LOCAL_DATA_PATH, prefixo="metas_resultados/")

    # 2. Microdados AEEB 2025
    print("\n📁 Upload: Microdados AEEB 2025")
    aeeb_dados = MICRODADOS_AEEB_PATH / "DADOS"
    upload_pasta(aeeb_dados, prefixo="aeeb2025/")

    # 3. Microdados Censo Escolar 2024
    print("\n📁 Upload: Microdados Censo Escolar 2024")
    censo_dados = MICRODADOS_CENSO_PATH / "microdados_censo_escolar_2024_defeso" / "dados"
    upload_pasta(censo_dados, prefixo="censo2024/")

    print("\n✅ Upload concluído.")


if __name__ == "__main__":
    main()
