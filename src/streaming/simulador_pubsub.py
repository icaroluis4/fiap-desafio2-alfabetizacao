"""Simulador de ingestão streaming via Pub/Sub.

Publica eventos near real-time de atualização de indicadores/metas de
alfabetização, usando amostra da camada Gold como base realista.

Uso:
    python src/streaming/simulador_pubsub.py
    python src/streaming/simulador_pubsub.py --n 20
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import bigquery, pubsub_v1

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    GCP_PROJECT_ID,
    BQ_DATASET_GOLD,
    PUBSUB_TOPIC_ID,
    PUBSUB_SUBSCRIPTION_ID,
)


def garantir_topico_e_sub(project_id: str, topic_id: str, subscription_id: str) -> str:
    """Cria tópico e subscription se não existirem. Retorna o path do tópico."""
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()

    topic_path = publisher.topic_path(project_id, topic_id)
    sub_path = subscriber.subscription_path(project_id, subscription_id)

    try:
        publisher.create_topic(request={"name": topic_path})
        print(f"✓ Tópico criado: {topic_path}")
    except AlreadyExists:
        print(f"• Tópico já existe: {topic_path}")

    try:
        subscriber.create_subscription(
            request={"name": sub_path, "topic": topic_path}
        )
        print(f"✓ Subscription criada: {sub_path}")
    except AlreadyExists:
        print(f"• Subscription já existe: {sub_path}")

    return topic_path


def carregar_amostra_municipios(n: int = 15) -> list[dict]:
    """Busca amostra de municípios na Gold para gerar eventos realistas."""
    client = bigquery.Client(project=GCP_PROJECT_ID)
    sql = f"""
    SELECT
      co_municipio,
      sg_uf,
      no_municipio,
      pc_alfabetizado_aeeb_2025,
      pc_alfabetizado_metas_2025,
      meta_2025,
      gap_meta_2025
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.indicador_municipio`
    WHERE pc_alfabetizado_aeeb_2025 IS NOT NULL
    ORDER BY RAND()
    LIMIT {int(n)}
    """
    rows = list(client.query(sql).result())
    return [dict(row.items()) for row in rows]


def montar_evento(row: dict, event_type: str) -> dict:
    """Monta payload de evento de streaming."""
    now = datetime.now(timezone.utc).isoformat()
    base = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "event_ts": now,
        "co_municipio": int(row["co_municipio"]) if row.get("co_municipio") is not None else None,
        "sg_uf": row.get("sg_uf"),
        "no_municipio": row.get("no_municipio"),
        "fonte": "simulador_streaming",
    }

    if event_type == "atualizacao_indicador":
        base.update(
            {
                "pc_alfabetizado": float(row["pc_alfabetizado_aeeb_2025"])
                if row.get("pc_alfabetizado_aeeb_2025") is not None
                else None,
                "meta_2025": float(row["meta_2025"]) if row.get("meta_2025") is not None else None,
                "gap_meta_2025": float(row["gap_meta_2025"])
                if row.get("gap_meta_2025") is not None
                else None,
            }
        )
    else:  # atualizacao_meta
        base.update(
            {
                "pc_alfabetizado": float(row["pc_alfabetizado_metas_2025"])
                if row.get("pc_alfabetizado_metas_2025") is not None
                else None,
                "meta_2025": float(row["meta_2025"]) if row.get("meta_2025") is not None else None,
                "gap_meta_2025": float(row["gap_meta_2025"])
                if row.get("gap_meta_2025") is not None
                else None,
            }
        )
    return base


def publicar_eventos(topic_path: str, eventos: list[dict]) -> int:
    """Publica lista de eventos no tópico Pub/Sub."""
    publisher = pubsub_v1.PublisherClient()
    futures = []

    for ev in eventos:
        data = json.dumps(ev, ensure_ascii=False).encode("utf-8")
        future = publisher.publish(
            topic_path,
            data,
            event_type=ev["event_type"],
            sg_uf=str(ev.get("sg_uf") or ""),
            fonte=ev.get("fonte", "simulador_streaming"),
        )
        futures.append((ev["event_id"], future))

    ok = 0
    for event_id, future in futures:
        try:
            msg_id = future.result(timeout=30)
            print(f"  ✓ event_id={event_id[:8]}… msg_id={msg_id}")
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ falha ao publicar {event_id}: {exc}")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulador Pub/Sub de alfabetização")
    parser.add_argument("--n", type=int, default=15, help="Qtd de municípios na amostra")
    args = parser.parse_args()

    if not GCP_PROJECT_ID:
        print("ERRO: GCP_PROJECT_ID não configurado")
        return 1

    print("=== Simulador de Streaming (Pub/Sub) ===\n")
    topic_path = garantir_topico_e_sub(
        GCP_PROJECT_ID, PUBSUB_TOPIC_ID, PUBSUB_SUBSCRIPTION_ID
    )

    print(f"\nCarregando amostra de {args.n} municípios da Gold...")
    amostra = carregar_amostra_municipios(args.n)
    if not amostra:
        print("ERRO: nenhuma linha retornada da Gold")
        return 1

    eventos: list[dict] = []
    for i, row in enumerate(amostra):
        # Alterna tipos de evento para simular mix realista
        event_type = "atualizacao_indicador" if i % 2 == 0 else "atualizacao_meta"
        eventos.append(montar_evento(row, event_type))

    print(f"Publicando {len(eventos)} eventos em {topic_path}...\n")
    ok = publicar_eventos(topic_path, eventos)
    print(f"\n✅ Publicados com sucesso: {ok}/{len(eventos)}")
    return 0 if ok == len(eventos) else 1


if __name__ == "__main__":
    raise SystemExit(main())
