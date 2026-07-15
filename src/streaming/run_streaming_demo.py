"""Demo end-to-end do fluxo híbrido de streaming.

1. Garante tópico/subscription
2. Publica eventos simulados
3. Consome e grava na Bronze

Uso:
    python src/streaming/run_streaming_demo.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(script: str, *args: str) -> int:
    cmd = [sys.executable, str(ROOT / script), *args]
    print(f"\n>>> {' '.join(cmd)}\n")
    return subprocess.call(cmd)


def main() -> int:
    print("=== Demo Streaming Híbrido (Pub/Sub → BigQuery) ===")
    rc1 = run("simulador_pubsub.py", "--n", "15")
    if rc1 != 0:
        return rc1
    rc2 = run("consumidor_bq.py", "--max", "50", "--timeout", "30")
    return rc2


if __name__ == "__main__":
    raise SystemExit(main())
