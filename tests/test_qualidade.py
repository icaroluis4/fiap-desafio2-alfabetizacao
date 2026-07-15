"""Testes leves de qualidade (smoke tests).

Os checks completos rodam via `src/qualidade/validacoes.py` no BigQuery.
Este módulo garante que o relatório e a estrutura de checks estão coerentes.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from qualidade.validacoes import CheckResult, RelatorioQualidade  # noqa: E402


def test_relatorio_contadores():
    rel = RelatorioQualidade()
    rel.add(CheckResult("a", "silver", "t1", "PASS", "ok", 0))
    rel.add(CheckResult("b", "gold", "t2", "WARN", "quase", 1))
    rel.add(CheckResult("c", "gold", "t3", "FAIL", "erro", 2))

    assert rel.n_pass == 1
    assert rel.n_warn == 1
    assert rel.n_fail == 1


def test_relatorio_markdown_contem_secoes():
    rel = RelatorioQualidade()
    rel.add(
        CheckResult(
            nome="nulos_em_co_municipio",
            camada="gold",
            tabela="indicador_municipio",
            status="PASS",
            detalhe="Registros com co_municipio nulo",
            valor=0,
        )
    )
    md = rel.to_markdown()
    assert "# Resultado da Auditoria de Qualidade" in md
    assert "nulos_em_co_municipio" in md
    assert "PASS" in md
