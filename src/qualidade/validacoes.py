"""Validações de qualidade de dados — Silver e Gold.

Cobertura (requisitos do challenge):
- Verificação de duplicidade
- Detecção de valores ausentes (chaves e métricas críticas)
- Validação de chaves de relacionamento
- Consistência entre tabelas / camadas
- Ranges de percentuais (0–100)

Uso:
    python src/qualidade/validacoes.py
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.cloud import bigquery

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import GCP_PROJECT_ID, BQ_DATASET_SILVER, BQ_DATASET_GOLD, REPO_ROOT


@dataclass
class CheckResult:
    nome: str
    camada: str
    tabela: str
    status: str  # PASS | WARN | FAIL
    detalhe: str
    valor: Any = None


@dataclass
class RelatorioQualidade:
    gerado_em: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resultados: list[CheckResult] = field(default_factory=list)

    def add(self, result: CheckResult) -> None:
        self.resultados.append(result)

    @property
    def n_pass(self) -> int:
        return sum(1 for r in self.resultados if r.status == "PASS")

    @property
    def n_warn(self) -> int:
        return sum(1 for r in self.resultados if r.status == "WARN")

    @property
    def n_fail(self) -> int:
        return sum(1 for r in self.resultados if r.status == "FAIL")

    def to_markdown(self) -> str:
        lines = [
            "# Resultado da Auditoria de Qualidade",
            "",
            f"- Gerado em (UTC): `{self.gerado_em}`",
            f"- Projeto: `{GCP_PROJECT_ID}`",
            f"- Resumo: **{self.n_pass} PASS** · **{self.n_warn} WARN** · **{self.n_fail} FAIL**",
            "",
            "| Status | Camada | Tabela | Check | Detalhe | Valor |",
            "|--------|--------|--------|-------|---------|-------|",
        ]
        for r in self.resultados:
            valor = "" if r.valor is None else str(r.valor)
            lines.append(
                f"| {r.status} | {r.camada} | `{r.tabela}` | {r.nome} | {r.detalhe} | {valor} |"
            )
        lines.extend(
            [
                "",
                "## Critérios aplicados",
                "",
                "1. **Nulos em chaves**: `co_municipio` / `co_uf` não podem ser nulos.",
                "2. **Duplicidade**: chaves de negócio não devem se repetir no grão esperado.",
                "3. **Range de percentuais**: valores de % devem estar entre 0 e 100 (quando não nulos).",
                "4. **Consistência entre camadas**: cobertura de join Gold com Metas e Censo.",
                "5. **Integridade referencial leve**: municípios da Gold devem existir na Silver AEEB.",
                "",
            ]
        )
        return "\n".join(lines)


def _scalar(client: bigquery.Client, sql: str) -> Any:
    rows = list(client.query(sql).result())
    if not rows:
        return None
    return list(rows[0].values())[0]


def _check_nulos_chave(
    client: bigquery.Client,
    rel: RelatorioQualidade,
    camada: str,
    dataset: str,
    tabela: str,
    coluna: str,
) -> None:
    sql = f"""
    SELECT COUNT(*) AS n
    FROM `{GCP_PROJECT_ID}.{dataset}.{tabela}`
    WHERE {coluna} IS NULL
    """
    n = _scalar(client, sql)
    status = "PASS" if n == 0 else "FAIL"
    rel.add(
        CheckResult(
            nome=f"nulos_em_{coluna}",
            camada=camada,
            tabela=tabela,
            status=status,
            detalhe=f"Registros com {coluna} nulo",
            valor=n,
        )
    )


def _check_duplicidade(
    client: bigquery.Client,
    rel: RelatorioQualidade,
    camada: str,
    dataset: str,
    tabela: str,
    chaves: list[str],
) -> None:
    cols = ", ".join(chaves)
    sql = f"""
    SELECT COUNT(*) AS n_dup
    FROM (
      SELECT {cols}, COUNT(*) AS c
      FROM `{GCP_PROJECT_ID}.{dataset}.{tabela}`
      GROUP BY {cols}
      HAVING c > 1
    )
    """
    n = _scalar(client, sql)
    status = "PASS" if n == 0 else "FAIL"
    rel.add(
        CheckResult(
            nome=f"duplicidade_{'+'.join(chaves)}",
            camada=camada,
            tabela=tabela,
            status=status,
            detalhe=f"Grupos duplicados pela chave ({cols})",
            valor=n,
        )
    )


def _check_range_percentual(
    client: bigquery.Client,
    rel: RelatorioQualidade,
    camada: str,
    dataset: str,
    tabela: str,
    coluna: str,
) -> None:
    sql = f"""
    SELECT COUNT(*) AS n
    FROM `{GCP_PROJECT_ID}.{dataset}.{tabela}`
    WHERE {coluna} IS NOT NULL
      AND ({coluna} < 0 OR {coluna} > 100)
    """
    n = _scalar(client, sql)
    status = "PASS" if n == 0 else "FAIL"
    rel.add(
        CheckResult(
            nome=f"range_0_100_{coluna}",
            camada=camada,
            tabela=tabela,
            status=status,
            detalhe=f"Valores de {coluna} fora de [0, 100]",
            valor=n,
        )
    )


def _check_volume_minimo(
    client: bigquery.Client,
    rel: RelatorioQualidade,
    camada: str,
    dataset: str,
    tabela: str,
    minimo: int,
) -> None:
    sql = f"SELECT COUNT(*) AS n FROM `{GCP_PROJECT_ID}.{dataset}.{tabela}`"
    n = _scalar(client, sql)
    status = "PASS" if n is not None and n >= minimo else "FAIL"
    rel.add(
        CheckResult(
            nome="volume_minimo",
            camada=camada,
            tabela=tabela,
            status=status,
            detalhe=f"Volume mínimo esperado >= {minimo}",
            valor=n,
        )
    )


def validar_silver(client: bigquery.Client, rel: RelatorioQualidade) -> None:
    # aeeb_municipio
    _check_volume_minimo(client, rel, "silver", BQ_DATASET_SILVER, "aeeb_municipio", 1000)
    _check_nulos_chave(client, rel, "silver", BQ_DATASET_SILVER, "aeeb_municipio", "co_municipio")
    _check_duplicidade(
        client,
        rel,
        "silver",
        BQ_DATASET_SILVER,
        "aeeb_municipio",
        ["co_municipio", "id_tipo_rede"],
    )
    _check_range_percentual(
        client, rel, "silver", BQ_DATASET_SILVER, "aeeb_municipio", "pc_aluno_alfabetizado"
    )

    # metas_municipios
    _check_volume_minimo(client, rel, "silver", BQ_DATASET_SILVER, "metas_municipios", 1000)
    _check_nulos_chave(client, rel, "silver", BQ_DATASET_SILVER, "metas_municipios", "co_municipio")
    _check_duplicidade(
        client,
        rel,
        "silver",
        BQ_DATASET_SILVER,
        "metas_municipios",
        ["co_municipio", "tp_rede"],
    )
    _check_range_percentual(
        client, rel, "silver", BQ_DATASET_SILVER, "metas_municipios", "pc_alfabetizado_2025"
    )
    _check_range_percentual(
        client, rel, "silver", BQ_DATASET_SILVER, "metas_municipios", "meta_2025"
    )

    # censo_escola
    _check_volume_minimo(client, rel, "silver", BQ_DATASET_SILVER, "censo_escola", 10000)
    _check_nulos_chave(client, rel, "silver", BQ_DATASET_SILVER, "censo_escola", "co_entidade")
    _check_duplicidade(
        client,
        rel,
        "silver",
        BQ_DATASET_SILVER,
        "censo_escola",
        ["co_entidade"],
    )

    # aeeb_estado / metas_ufs
    _check_nulos_chave(client, rel, "silver", BQ_DATASET_SILVER, "aeeb_estado", "co_uf")
    _check_nulos_chave(client, rel, "silver", BQ_DATASET_SILVER, "metas_ufs", "co_uf")


def validar_gold(client: bigquery.Client, rel: RelatorioQualidade) -> None:
    # Volumes
    _check_volume_minimo(client, rel, "gold", BQ_DATASET_GOLD, "indicador_municipio", 1000)
    _check_volume_minimo(client, rel, "gold", BQ_DATASET_GOLD, "metas_vs_resultados", 1000)
    _check_volume_minimo(client, rel, "gold", BQ_DATASET_GOLD, "indicador_uf", 20)

    # Chaves e duplicidade
    _check_nulos_chave(client, rel, "gold", BQ_DATASET_GOLD, "indicador_municipio", "co_municipio")
    _check_duplicidade(
        client,
        rel,
        "gold",
        BQ_DATASET_GOLD,
        "indicador_municipio",
        ["co_municipio"],
    )
    _check_nulos_chave(client, rel, "gold", BQ_DATASET_GOLD, "indicador_uf", "co_uf")
    _check_duplicidade(
        client,
        rel,
        "gold",
        BQ_DATASET_GOLD,
        "indicador_uf",
        ["co_uf"],
    )

    # Ranges
    _check_range_percentual(
        client,
        rel,
        "gold",
        BQ_DATASET_GOLD,
        "indicador_municipio",
        "pc_alfabetizado_aeeb_2025",
    )
    _check_range_percentual(
        client,
        rel,
        "gold",
        BQ_DATASET_GOLD,
        "indicador_municipio",
        "pc_alfabetizado_metas_2025",
    )

    # Cobertura de joins (WARN se < 95%, FAIL se < 80%)
    sql_cobertura = f"""
    SELECT
      COUNT(*) AS total,
      COUNTIF(pc_alfabetizado_metas_2025 IS NOT NULL) AS com_metas,
      COUNTIF(qtd_escolas IS NOT NULL) AS com_censo
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.indicador_municipio`
    """
    row = list(client.query(sql_cobertura).result())[0]
    total = row.total or 0
    pct_metas = (row.com_metas / total * 100) if total else 0
    pct_censo = (row.com_censo / total * 100) if total else 0

    def _status_cobertura(pct: float) -> str:
        if pct >= 95:
            return "PASS"
        if pct >= 80:
            return "WARN"
        return "FAIL"

    rel.add(
        CheckResult(
            nome="cobertura_join_metas",
            camada="gold",
            tabela="indicador_municipio",
            status=_status_cobertura(pct_metas),
            detalhe="% municípios com match em Metas",
            valor=round(pct_metas, 2),
        )
    )
    rel.add(
        CheckResult(
            nome="cobertura_join_censo",
            camada="gold",
            tabela="indicador_municipio",
            status=_status_cobertura(pct_censo),
            detalhe="% municípios com match em Censo",
            valor=round(pct_censo, 2),
        )
    )

    # Integridade referencial: todo município Gold deve existir no AEEB Silver (rede municipal)
    sql_orfao = f"""
    SELECT COUNT(*) AS n
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.indicador_municipio` g
    LEFT JOIN `{GCP_PROJECT_ID}.{BQ_DATASET_SILVER}.aeeb_municipio` s
      ON g.co_municipio = s.co_municipio
     AND s.id_tipo_rede = 3
    WHERE s.co_municipio IS NULL
    """
    n_orfao = _scalar(client, sql_orfao)
    rel.add(
        CheckResult(
            nome="integridade_gold_em_aeeb_silver",
            camada="gold",
            tabela="indicador_municipio",
            status="PASS" if n_orfao == 0 else "FAIL",
            detalhe="Municípios Gold sem correspondente em silver.aeeb_municipio (rede 3)",
            valor=n_orfao,
        )
    )

    # Consistência gap: se meta e resultado existem, gap deve ser resultado - meta
    sql_gap = f"""
    SELECT COUNT(*) AS n
    FROM `{GCP_PROJECT_ID}.{BQ_DATASET_GOLD}.indicador_municipio`
    WHERE pc_alfabetizado_metas_2025 IS NOT NULL
      AND meta_2025 IS NOT NULL
      AND gap_meta_2025 IS NOT NULL
      AND ABS(gap_meta_2025 - (pc_alfabetizado_metas_2025 - meta_2025)) > 0.05
    """
    n_gap = _scalar(client, sql_gap)
    rel.add(
        CheckResult(
            nome="consistencia_calculo_gap_meta_2025",
            camada="gold",
            tabela="indicador_municipio",
            status="PASS" if n_gap == 0 else "FAIL",
            detalhe="Linhas com gap_meta_2025 inconsistente (tol. 0.05)",
            valor=n_gap,
        )
    )


def salvar_relatorio(rel: RelatorioQualidade) -> Path:
    out_dir = REPO_ROOT / "docs" / "evidencias"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "resultado_auditoria.md"
    out_path.write_text(rel.to_markdown(), encoding="utf-8")
    return out_path


def main() -> int:
    if not GCP_PROJECT_ID:
        print("ERRO: GCP_PROJECT_ID não configurado no .env")
        return 1

    print("Executando validações de qualidade (Silver + Gold)...\n")
    client = bigquery.Client(project=GCP_PROJECT_ID)
    rel = RelatorioQualidade()

    validar_silver(client, rel)
    validar_gold(client, rel)

    # Console
    for r in rel.resultados:
        icon = {"PASS": "✓", "WARN": "!", "FAIL": "✗"}.get(r.status, "?")
        print(f"[{icon}] {r.status:4} | {r.camada:6} | {r.tabela:22} | {r.nome}: {r.detalhe} => {r.valor}")

    print(
        f"\nResumo: {rel.n_pass} PASS · {rel.n_warn} WARN · {rel.n_fail} FAIL "
        f"(total {len(rel.resultados)} checks)"
    )

    path = salvar_relatorio(rel)
    print(f"Relatório salvo em: {path}")

    # Exit code: falha se houver FAIL
    return 1 if rel.n_fail > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
