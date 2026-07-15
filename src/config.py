"""Centraliza configurações do projeto."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega variáveis do .env (se existir)
load_dotenv()

# ---------------------------------------------------------------------------
# GCP
# ---------------------------------------------------------------------------
GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
GCP_LOCATION: str = os.getenv("GCP_LOCATION", "US")

GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "")

BQ_DATASET_BRONZE: str = os.getenv("BQ_DATASET_BRONZE", "bronze_alfabetizacao")
BQ_DATASET_SILVER: str = os.getenv("BQ_DATASET_SILVER", "silver_alfabetizacao")
BQ_DATASET_GOLD: str = os.getenv("BQ_DATASET_GOLD", "gold_alfabetizacao")

# ---------------------------------------------------------------------------
# Streaming (Pub/Sub)
# ---------------------------------------------------------------------------
PUBSUB_TOPIC_ID: str = os.getenv("PUBSUB_TOPIC_ID", "alfabetizacao-eventos")
PUBSUB_SUBSCRIPTION_ID: str = os.getenv(
    "PUBSUB_SUBSCRIPTION_ID", "alfabetizacao-eventos-sub"
)
BQ_TABLE_STREAMING: str = os.getenv("BQ_TABLE_STREAMING", "eventos_streaming")

# ---------------------------------------------------------------------------
# Caminhos locais
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent

LOCAL_DATA_PATH: Path = Path(os.getenv("LOCAL_DATA_PATH", REPO_ROOT.parent / "converted_csv"))
MICRODADOS_AEEB_PATH: Path = Path(os.getenv("MICRODADOS_AEEB_PATH", REPO_ROOT.parent / "microdados_AEEB_2025"))
MICRODADOS_CENSO_PATH: Path = Path(os.getenv("MICRODADOS_CENSO_PATH", REPO_ROOT.parent / "microdados_censo_escolar_2024"))
