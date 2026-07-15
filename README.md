# FIAP Desafio 2 — Pipeline de Alfabetização no Brasil

Pipeline híbrida (batch + streaming) para análise do **Indicador Criança Alfabetizada**, com arquitetura medalhão (**Bronze / Silver / Gold**) no **GCP / BigQuery**.

> Tech Challenge — Fase 2 · Pós-graduação em Arquitetura de Big Data (FIAP)

---

## 1. Contexto do problema

A alfabetização na infância é prioridade de política pública no Brasil, materializada no **Compromisso Nacional Criança Alfabetizada**. A meta nacional é que, até **2030**, todas as crianças estejam alfabetizadas ao final do 2º ano do ensino fundamental.

O **Indicador Criança Alfabetizada** expressa o percentual de estudantes que atingem o ponto de corte de proficiência. Analisar esse indicador de forma isolada é insuficiente: é preciso integrar **resultados**, **metas** e **contexto escolar** para subsidiar decisões baseadas em evidência.

Este projeto constrói uma pipeline em nuvem que:

- ingere fontes educacionais públicas;
- padroniza e integra as bases;
- disponibiliza uma camada analítica confiável por município e UF;
- contempla ingestão batch e streaming;
- aplica validações de qualidade de dados.

---

## 2. Arquitetura (visão geral)

```
Fontes públicas (INEP)
        |
        |- Batch --> GCS (landing) --> BigQuery Bronze
        |                                      |
        +- Streaming (Pub/Sub) --------------->|
                                               v
                                         BigQuery Silver
                                          (limpo / padronizado)
                                               v
                                          BigQuery Gold
                                    (indicadores analíticos)
                                               |
                          +--------------------+--------------------+
                          v                    v                    v
                     Dashboards          Análises / IA         Políticas públicas
```

| Camada | Papel | Exemplos |
|--------|-------|----------|
| **Bronze** | Dados brutos, sem transformação pesada | CSVs no GCS + tabelas raw no BQ + `eventos_streaming` |
| **Silver** | Limpeza, tipos, chaves, subset analítico | `aeeb_municipio`, `metas_municipios`, `censo_escola` |
| **Gold** | Produto analítico integrado | `indicador_municipio`, `metas_vs_resultados`, `indicador_uf` |

Detalhamento das escolhas: [`docs/decisoes_tecnicas.md`](docs/decisoes_tecnicas.md)  
Evidências de execução: [`docs/evidencias/`](docs/evidencias/)

---

## 3. Fontes de dados

| Fonte | Papel | Uso na pipeline |
|-------|-------|-----------------|
| **AEEB 2025 (INEP)** | Base principal do indicador | Silver/Gold — `% alfabetizados`, níveis, média LP |
| **Metas e Resultados (INEP)** | Metas municipais/estaduais e série histórica | Silver/Gold — meta vs resultado, evolução |
| **Censo Escolar 2024 (INEP)** | Enriquecimento de contexto escolar | Silver/Gold — escolas, matrículas, infraestrutura |
| **Base dos Dados / BQ público** | Referência de schema e validação conceitual | Não é a ingestão primária deste MVP |

---

## 4. Fluxo de dados

### Batch
1. Upload dos CSVs locais para o bucket GCS  
2. Load GCS → tabelas `bronze_alfabetizacao.*`  
3. Transformações SQL via Python → `silver_alfabetizacao.*`  
4. Integração analítica → `gold_alfabetizacao.*`  
5. Validações de qualidade sobre Silver/Gold  

### Streaming
1. Simulador publica eventos (`atualizacao_indicador` / `atualizacao_meta`) no **Pub/Sub**  
2. Consumidor grava em `bronze_alfabetizacao.eventos_streaming`  
3. Demonstra o padrão híbrido near real-time sem substituir o batch histórico  

---

## 5. Camada Gold (produto analítico)

| Tabela | Grão | Conteúdo |
|--------|------|----------|
| `indicador_municipio` | Município | AEEB + Metas + Censo + gap/evolução |
| `metas_vs_resultados` | Município e UF | Comparativo meta × resultado |
| `indicador_uf` | UF | Consolidado estadual + % municípios que atingiram meta |

Métricas derivadas principais: `gap_meta_2025`, `atingiu_meta_2025`, `evolucao_2023_2025`, `alunos_por_docente_ai`.

---

## 6. Qualidade de dados

Script: `src/qualidade/validacoes.py`  
Evidência: `docs/evidencias/resultado_auditoria.md`

Checks:
- nulos em chaves
- duplicidade por grão de negócio
- ranges de percentuais (0–100)
- cobertura de joins Gold ↔ Metas/Censo
- integridade Gold → Silver
- consistência do cálculo de gap

**Última execução:** 27 PASS · 0 WARN · 0 FAIL

---

## 7. Tecnologias

| Componente | Tecnologia |
|------------|------------|
| Cloud | GCP |
| Storage bruto | Cloud Storage (GCS) |
| Warehouse | BigQuery |
| Streaming | Pub/Sub |
| Orquestração do MVP | Scripts Python + ADC |
| Qualidade | Python + queries BQ |
| Versionamento | Git (branches de feature) |

Justificativas e trade-offs: [`docs/decisoes_tecnicas.md`](docs/decisoes_tecnicas.md)

---

## 8. Estrutura do repositório

```
fiap-desafio2-alfabetizacao/
├── docs/
│   ├── decisoes_tecnicas.md
│   ├── diagramas/
│   └── evidencias/
├── src/
│   ├── config.py
│   ├── infra/           # bucket e datasets
│   ├── ingestao/        # upload GCS + load Bronze
│   ├── transformacao/   # Silver + Gold
│   ├── qualidade/       # validações
│   └── streaming/       # Pub/Sub → Bronze
├── tests/
├── notebooks/
└── requirements.txt
```

---

## 9. Como executar (resumo)

```bash
# Ambiente
pip install -r requirements.txt
# Autenticação GCP
gcloud auth application-default login

# Infra (se necessário)
python src/infra/criar_bucket_gcs.py
python src/infra/criar_datasets_bq.py

# Batch → Bronze
python src/ingestao/upload_gcs.py
python src/ingestao/bq_load_bronze.py

# Silver
python src/transformacao/silver_metas.py
python src/transformacao/silver_aeeb.py
python src/transformacao/silver_censo.py

# Gold
python src/transformacao/gold_indicadores.py

# Qualidade
python src/qualidade/validacoes.py

# Streaming (demo)
python src/streaming/run_streaming_demo.py
```

> Configure o `.env` a partir do `.env-example` antes de executar.

---

## 10. Aplicação em IA (potencial da Gold)

A camada Gold está pronta para usos de ciência de dados / IA, por exemplo:

1. **Predição de risco de não atingimento de meta** por município  
2. **Clusterização de vulnerabilidade educacional** (resultado + infraestrutura + matrícula)  
3. **Priorização de intervenção** (ranking por gap, evolução e contexto escolar)  

Esses usos não fazem parte do MVP de engenharia, mas orientam o desenho da Gold.

---

## 11. FinOps

A arquitetura considera eficiência de custo no GCP (volume controlado, camadas com responsabilidades distintas e consultas analíticas na Gold).  
O detalhamento de FinOps será aprofundado em documentação específica.

---

## 12. Limitações do MVP

- Streaming é **simulado e demonstrável**, não um barramento 24/7 de produção  
- Grão analítico principal é **município/UF** (não aluno na Gold)  
- Sem orquestrador tipo Airflow/Composer neste momento  
- README + decisões técnicas concentram a narrativa; diagrama visual em `docs/diagramas/`

---

## 13. Vídeo executivo

Vídeo de apresentação da solução (não listado):

- [Assistir no YouTube](https://www.youtube.com/watch?v=WAQPlCF5w1s)

Slides da apresentação em PDF: [`docs/presentation/`](docs/presentation/)

---

## 14. Equipe / entrega

Projeto desenvolvido para o **Tech Challenge da Fase 2** da pós-graduação em Arquitetura de Big Data — FIAP.

Documentos relacionados:
- [`docs/decisoes_tecnicas.md`](docs/decisoes_tecnicas.md)
- [`docs/evidencias/resultado_auditoria.md`](docs/evidencias/resultado_auditoria.md)
- [`docs/diagramas/`](docs/diagramas/)
- [`docs/presentation/`](docs/presentation/)
