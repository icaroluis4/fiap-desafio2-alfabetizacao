# Resultado da Auditoria de Qualidade

- Gerado em (UTC): `2026-07-15T00:55:40.515545+00:00`
- Projeto: `semiotic-primer-366516`
- Resumo: **27 PASS** · **0 WARN** · **0 FAIL**

| Status | Camada | Tabela | Check | Detalhe | Valor |
|--------|--------|--------|-------|---------|-------|
| PASS | silver | `aeeb_municipio` | volume_minimo | Volume mínimo esperado >= 1000 | 12416 |
| PASS | silver | `aeeb_municipio` | nulos_em_co_municipio | Registros com co_municipio nulo | 0 |
| PASS | silver | `aeeb_municipio` | duplicidade_co_municipio+id_tipo_rede | Grupos duplicados pela chave (co_municipio, id_tipo_rede) | 0 |
| PASS | silver | `aeeb_municipio` | range_0_100_pc_aluno_alfabetizado | Valores de pc_aluno_alfabetizado fora de [0, 100] | 0 |
| PASS | silver | `metas_municipios` | volume_minimo | Volume mínimo esperado >= 1000 | 5466 |
| PASS | silver | `metas_municipios` | nulos_em_co_municipio | Registros com co_municipio nulo | 0 |
| PASS | silver | `metas_municipios` | duplicidade_co_municipio+tp_rede | Grupos duplicados pela chave (co_municipio, tp_rede) | 0 |
| PASS | silver | `metas_municipios` | range_0_100_pc_alfabetizado_2025 | Valores de pc_alfabetizado_2025 fora de [0, 100] | 0 |
| PASS | silver | `metas_municipios` | range_0_100_meta_2025 | Valores de meta_2025 fora de [0, 100] | 0 |
| PASS | silver | `censo_escola` | volume_minimo | Volume mínimo esperado >= 10000 | 215545 |
| PASS | silver | `censo_escola` | nulos_em_co_entidade | Registros com co_entidade nulo | 0 |
| PASS | silver | `censo_escola` | duplicidade_co_entidade | Grupos duplicados pela chave (co_entidade) | 0 |
| PASS | silver | `aeeb_estado` | nulos_em_co_uf | Registros com co_uf nulo | 0 |
| PASS | silver | `metas_ufs` | nulos_em_co_uf | Registros com co_uf nulo | 0 |
| PASS | gold | `indicador_municipio` | volume_minimo | Volume mínimo esperado >= 1000 | 5500 |
| PASS | gold | `metas_vs_resultados` | volume_minimo | Volume mínimo esperado >= 1000 | 5444 |
| PASS | gold | `indicador_uf` | volume_minimo | Volume mínimo esperado >= 20 | 27 |
| PASS | gold | `indicador_municipio` | nulos_em_co_municipio | Registros com co_municipio nulo | 0 |
| PASS | gold | `indicador_municipio` | duplicidade_co_municipio | Grupos duplicados pela chave (co_municipio) | 0 |
| PASS | gold | `indicador_uf` | nulos_em_co_uf | Registros com co_uf nulo | 0 |
| PASS | gold | `indicador_uf` | duplicidade_co_uf | Grupos duplicados pela chave (co_uf) | 0 |
| PASS | gold | `indicador_municipio` | range_0_100_pc_alfabetizado_aeeb_2025 | Valores de pc_alfabetizado_aeeb_2025 fora de [0, 100] | 0 |
| PASS | gold | `indicador_municipio` | range_0_100_pc_alfabetizado_metas_2025 | Valores de pc_alfabetizado_metas_2025 fora de [0, 100] | 0 |
| PASS | gold | `indicador_municipio` | cobertura_join_metas | % municípios com match em Metas | 99.33 |
| PASS | gold | `indicador_municipio` | cobertura_join_censo | % municípios com match em Censo | 99.98 |
| PASS | gold | `indicador_municipio` | integridade_gold_em_aeeb_silver | Municípios Gold sem correspondente em silver.aeeb_municipio (rede 3) | 0 |
| PASS | gold | `indicador_municipio` | consistencia_calculo_gap_meta_2025 | Linhas com gap_meta_2025 inconsistente (tol. 0.05) | 0 |

## Critérios aplicados

1. **Nulos em chaves**: `co_municipio` / `co_uf` não podem ser nulos.
2. **Duplicidade**: chaves de negócio não devem se repetir no grão esperado.
3. **Range de percentuais**: valores de % devem estar entre 0 e 100 (quando não nulos).
4. **Consistência entre camadas**: cobertura de join Gold com Metas e Censo.
5. **Integridade referencial leve**: municípios da Gold devem existir na Silver AEEB.
