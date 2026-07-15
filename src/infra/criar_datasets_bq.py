"""Cria datasets no BigQuery para as camadas Bronze, Silver e Gold."""
from __future__ import annotations

import sys
from pathlib import Path

from google.cloud import bigquery
from google.api_core.exceptions import Conflict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    GCP_PROJECT_ID,
    GCP_LOCATION,
    BQ_DATASET_BRONZE,
    BQ_DATASET_SILVER,
    BQ_DATASET_GOLD,
)


def criar_dataset(
    dataset_id: str,
    project_id: str = GCP_PROJECT_ID,
    location: str = GCP_LOCATION,
    description: str = "",
) -> str:
    """Cria um dataset no BigQuery se não existir.

    Args:
        dataset_id: ID do dataset (ex: bronze_alfabetizacao).
        project_id: ID do projeto GCP.
        location: Região do dataset.
        description: Descrição do dataset.

    Returns:
        ID completo do dataset (project.dataset).
    """
    if not project_id:
        raise ValueError("GCP_PROJECT_ID deve estar configurado.")

    client = bigquery.Client(project=project_id)
    dataset_ref = f"{project_id}.{dataset_id}"

    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset '{dataset_ref}' já existe.")
        return dataset_ref
    except Exception:
        pass  # Dataset não existe, prosseguir com criação

    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = location
    dataset.description = description

    # Configurações de expiração de tabelas (opcional — FinOps)
    # dataset.default_table_expiration_ms = 30 * 24 * 60 * 60 * 1000  # 30 dias

    new_dataset = client.create_dataset(dataset, exists_ok=True)
    print(f"Dataset '{new_dataset.dataset_id}' criado em {new_dataset.location}.")
    return dataset_ref


def main() -> None:
    """Cria os três datasets da arquitetura medalhão."""
    datasets = [
        (BQ_DATASET_BRONZE, "Camada Bronze — dados brutos ingeridos do GCS"),
        (BQ_DATASET_SILVER, "Camada Silver — dados limpos, padronizados e integrados"),
        (BQ_DATASET_GOLD, "Camada Gold — agregações analíticas e indicadores"),
    ]

    for dataset_id, description in datasets:
        try:
            criar_dataset(dataset_id, description=description)
        except Exception as exc:
            print(f"Erro ao criar dataset '{dataset_id}': {exc}")
            sys.exit(1)

    print("\nTodos os datasets foram verificados/criados com sucesso.")


if __name__ == "__main__":
    main()
