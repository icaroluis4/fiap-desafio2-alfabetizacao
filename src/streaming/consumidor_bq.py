"""Consome eventos do Pub/Sub e grava na Bronze (BigQuery).

Cria a tabela `bronze_alfabetizacao.eventos_streaming` se necessário e
insere os eventos consumidos da subscription.

Uso:
    python src/streaming/consumidor_bq.py
    python src/streaming/consumidor_bq.py --max 50 --timeout 20
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.api_core.exceptions import NotFound
from google.cloud import bigquery, pubsub_v1

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    GCP_PROJECT_ID,
    BQ_DATASET_BRONZE,
    PUBSUB_SUBSCRIPTION_ID,
    BQ_TABLE_STREAMING,
)


SCHEMA = [
    bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("event_type", "STRING"),
    bigquery.SchemaField("event_ts", "TIMESTAMP"),
    bigquery.SchemaField("ingest_ts", "TIMESTAMP"),
    bigquery.SchemaField("co_municipio", "INT64"),
    bigquery.SchemaField("sg_uf", "STRING"),
    bigquery.SchemaField("no_municipio", "STRING"),
    bigquery.SchemaField("pc_alfabetizado", "FLOAT64"),
    bigquery.SchemaField("meta_2025", "FLOAT64"),
    bigquery.SchemaField("gap_meta_2025", "FLOAT64"),
    bigquery.SchemaField("fonte", "STRING"),
    bigquery.SchemaField("payload_json", "STRING"),
    bigquery.SchemaField("pubsub_message_id", "STRING"),
]


def garantir_tabela_streaming(client: bigquery.Client) -> str:
    """Garante existência da tabela Bronze de eventos streaming."""
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET_BRONZE}.{BQ_TABLE_STREAMING}"
    try:
        client.get_table(table_id)
        print(f"• Tabela já existe: {table_id}")
    except NotFound:
        table = bigquery.Table(table_id, schema=SCHEMA)
        table.description = (
            "Eventos de streaming simulados (atualização de indicadores/metas)"
        )
        client.create_table(table)
        print(f"✓ Tabela criada: {table_id}")
    return table_id


def parse_evento(message: pubsub_v1.subscriber.message.Message) -> dict[str, Any]:
    """Converte mensagem Pub/Sub em linha para BigQuery."""
    raw = message.data.decode("utf-8")
    payload = json.loads(raw)
    ingest_ts = datetime.now(timezone.utc).isoformat()

    return {
        "event_id": payload.get("event_id") or message.message_id,
        "event_type": payload.get("event_type"),
        "event_ts": payload.get("event_ts"),
        "ingest_ts": ingest_ts,
        "co_municipio": payload.get("co_municipio"),
        "sg_uf": payload.get("sg_uf"),
        "no_municipio": payload.get("no_municipio"),
        "pc_alfabetizado": payload.get("pc_alfabetizado"),
        "meta_2025": payload.get("meta_2025"),
        "gap_meta_2025": payload.get("gap_meta_2025"),
        "fonte": payload.get("fonte", "simulador_streaming"),
        "payload_json": raw,
        "pubsub_message_id": message.message_id,
    }


def consumir_e_gravar(max_messages: int, timeout: float) -> int:
    """Puxa mensagens da subscription e grava no BigQuery. Retorna qtd inserida."""
    bq = bigquery.Client(project=GCP_PROJECT_ID)
    table_id = garantir_tabela_streaming(bq)

    subscriber = pubsub_v1.SubscriberClient()
    sub_path = subscriber.subscription_path(GCP_PROJECT_ID, PUBSUB_SUBSCRIPTION_ID)

    print(f"\nConsumindo até {max_messages} mensagens (timeout={timeout}s)...")
    response = subscriber.pull(
        request={
            "subscription": sub_path,
            "max_messages": max_messages,
        },
        timeout=timeout,
    )

    received = response.received_messages
    if not received:
        print("Nenhuma mensagem disponível na subscription.")
        return 0

    rows: list[dict[str, Any]] = []
    ack_ids: list[str] = []

    for rm in received:
        try:
            row = parse_evento(rm.message)
            rows.append(row)
            ack_ids.append(rm.ack_id)
            print(
                f"  • {row['event_type']} | {row['sg_uf']} | "
                f"{row['no_municipio']} | pc={row['pc_alfabetizado']}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ erro ao parsear mensagem {rm.message.message_id}: {exc}")

    if not rows:
        return 0

    errors = bq.insert_rows_json(table_id, rows)
    if errors:
        print(f"ERRO no insert BigQuery: {errors}")
        return 0

    # Ack só após insert bem-sucedido
    subscriber.acknowledge(
        request={"subscription": sub_path, "ack_ids": ack_ids}
    )
    print(f"\n✓ {len(rows)} eventos inseridos em {table_id}")
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Consumidor Pub/Sub → BigQuery Bronze")
    parser.add_argument("--max", type=int, default=50, help="Máx. mensagens por pull")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout do pull (s)")
    args = parser.parse_args()

    if not GCP_PROJECT_ID:
        print("ERRO: GCP_PROJECT_ID não configurado")
        return 1

    print("=== Consumidor Streaming → Bronze ===")
    n = consumir_e_gravar(args.max, args.timeout)

    # Contagem final
    bq = bigquery.Client(project=GCP_PROJECT_ID)
    table_id = f"{GCP_PROJECT_ID}.{BQ_DATASET_BRONZE}.{BQ_TABLE_STREAMING}"
    try:
        total = list(
            bq.query(f"SELECT COUNT(*) AS n FROM `{table_id}`").result()
        )[0].n
        print(f"Total na tabela streaming: {total}")
    except Exception:  # noqa: BLE001
        pass

    print("\n✅ Consumo finalizado." if n > 0 else "\n⚠ Nenhum evento consumido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
