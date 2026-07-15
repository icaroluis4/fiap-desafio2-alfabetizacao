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

## 11. FinOps — decisões de custo desta pipeline

O FinOps aqui não é checklist genérico: são **escolhas concretas** tomadas no desenho e na implementação, com impacto mensurável no volume processado e no padrão de consulta.

### 11.1 Perfil de custo do MVP

| Componente | O que existe no projeto | Implicação de custo |
|------------|-------------------------|---------------------|
| GCS (landing) | Bucket `fiap-desafio2-bronze-alfabetizacao` com CSVs brutos | Storage barato do bruto; evita reupload a cada transformação |
| BigQuery Bronze | ~10 tabelas raw (inclui `aeeb_ts_aluno` com **2,2M** linhas) | Histórico preservado, mas **não** é a camada de consulta analítica |
| BigQuery Silver | Subset limpo (ex.: Censo com colunas selecionadas, não 426) | Menos bytes lidos em transformações e auditorias |
| BigQuery Gold | 3 tabelas enxutas (`indicador_municipio` ~5,5k; `indicador_uf` 27) | Consultas de negócio varrem **milhares**, não milhões de linhas |
| Pub/Sub | Tópico + subscription de demo (dezenas de eventos) | Streaming demonstrável sem fila/consumo contínuo 24/7 |
| Compute | Scripts Python locais + jobs BQ sob demanda | Sem cluster sempre ligado (Dataproc/Composer/VMs ociosas) |

Ordem de grandeza de storage do recorte trabalhado: **centenas de MB** (não dezenas de GB). Isso cabe com folga no free tier típico de storage do BQ/GCS para o volume acadêmico — o ponto FinOps não é “é de graça”, é **não crescer custo sem necessidade**.

### 11.2 Decisões que reduzem custo (e o que foi evitado)

1. **Consultar Gold/Silver, não a Bronze crua**  
   A Bronze guarda fidelidade (incluindo microdado aluno). Análises e validações de negócio rodam sobre Silver/Gold.  
   **Evitado:** dashboard ou notebook varrendo `aeeb_ts_aluno` (2,2M) a cada pergunta.

2. **Grão municipal na Gold, não aluno**  
   O indicador e as metas de política pública são municipais/estaduais.  
   **Evitado:** materializar Gold em grão aluno/escola sem demanda do MVP (explodiria storage e scan).

3. **Subset do Censo na Silver**  
   Do arquivo com centenas de colunas, a Silver mantém identificação, dependência, matrículas de anos iniciais e flags de infraestrutura relevantes.  
   **Evitado:** `SELECT *` do Censo em toda transformação.

4. **Landing no GCS + load controlado no BQ**  
   Bruto fica no Storage; o BQ recebe cargas sob demanda via scripts.  
   **Evitado:** reprocessar arquivo local gigante a cada experimento sem versionar o landing.

5. **Streaming sob demanda, não consumidor sempre ativo**  
   Pub/Sub + pull/insert demonstram o padrão híbrido; não há worker 24/7 nem Dataflow contínuo.  
   **Evitado:** custo fixo de streaming ocioso só para “ter streaming”.

6. **Sem orquestrador gerenciado no MVP**  
   Fluxo por scripts versionados.  
   **Evitado:** Cloud Composer/Airflow gerenciado (custo base relevante) antes de haver SLA de produção.

7. **Qualidade com checks pontuais no BQ**  
   `validacoes.py` executa contagens/agregações objetivas e gera evidência.  
   **Evitado:** ferramentas caras de observability só para o escopo acadêmico.

### 11.3 Onde o custo ainda pode subir (e como controlamos)

| Risco | Como aparece | Controle adotado / recomendado |
|-------|--------------|--------------------------------|
| Scan acidental da Bronze | Query exploratória em tabela raw larga | Disciplina de camada: análise na Gold; Bronze só reprocessamento |
| Reprocessar TS_ALUNO sem necessidade | Reload completo do microdado | Manter aluno na Bronze/GCS; Gold usa agregado municipal |
| Streaming “sempre ligado” | Subscriber/Dataflow ocioso | Demo sob demanda (`run_streaming_demo.py`) |
| Crescimento de evidências/logs | Prints e tabelas auxiliares | Evidências no Git; dados de negócio no GCP com datasets separados |
| Orquestração prematura | Composer “porque é best practice” | Só evoluir quando houver agendamento real e dono operacional |

### 11.4 Princípio FinOps do projeto

> **Pagar por valor analítico, não por volume bruto.**  
> O bruto (Bronze/GCS) existe para rastreabilidade. O custo recorrente de análise deve cair sobre tabelas pequenas, estáveis e com pergunta de negócio clara (Gold).

Detalhamento das decisões de arquitetura ligadas a isso: [`docs/decisoes_tecnicas.md`](docs/decisoes_tecnicas.md).

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
