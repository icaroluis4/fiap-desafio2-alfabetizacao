"""Cria bucket no Google Cloud Storage para a camada Bronze."""
from __future__ import annotations

import sys

from google.cloud import storage
from google.api_core.exceptions import Conflict

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import GCP_PROJECT_ID, GCS_BUCKET_NAME, GCP_LOCATION


def criar_bucket(
    project_id: str = GCP_PROJECT_ID,
    bucket_name: str = GCS_BUCKET_NAME,
    location: str = GCP_LOCATION,
    storage_class: str = "STANDARD",
) -> str:
    """Cria um bucket no GCS se ele não existir.

    Args:
        project_id: ID do projeto GCP.
        bucket_name: Nome único do bucket.
        location: Região do bucket (ex: US, southamerica-east1).
        storage_class: Classe de armazenamento (STANDARD, NEARLINE, etc.).

    Returns:
        URL do bucket criado ou existente.
    """
    if not project_id or not bucket_name:
        raise ValueError("GCP_PROJECT_ID e GCS_BUCKET_NAME devem estar configurados.")

    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)

    if bucket.exists():
        print(f"Bucket '{bucket_name}' já existe.")
        return f"gs://{bucket_name}"

    bucket.storage_class = storage_class
    new_bucket = client.create_bucket(bucket, location=location)

    print(f"Bucket '{new_bucket.name}' criado em {new_bucket.location}.")
    return f"gs://{new_bucket.name}"


if __name__ == "__main__":
    try:
        url = criar_bucket()
        print(f"URL: {url}")
    except Exception as exc:
        print(f"Erro ao criar bucket: {exc}")
        sys.exit(1)
