# Decisões Técnicas

Documento de apoio ao README. Explica **o que foi decidido**, **por quê** e **qual o trade-off**, com base na implementação real da pipeline no GCP.

Projeto GCP: `semiotic-primer-366516`  
Datasets: `bronze_alfabetizacao` · `silver_alfabetizacao` · `gold_alfabetizacao`  
Bucket: `gs://fiap-desafio2-bronze-alfabetizacao`

---

## 1. Problema de arquitetura

O desafio exige uma pipeline em nuvem capaz de:

1. integrar fontes educacionais heterogêneas;
2. seguir arquitetura medalhão;
3. combinar ingestão **batch** e **streaming**;
4. garantir qualidade e rastreabilidade;
5. gerar camada analítica útil para análise e, potencialmente, IA.

O desenho parte do problema de negócio (indicador de alfabetização + metas + contexto escolar), não da ferramenta.

---

## 2. Decisões principais

### D1. Plataforma: GCP + BigQuery

**Decisão:** implementar a solução no Google Cloud Platform, com BigQuery como motor analítico principal.

**Por quê:**
- SQL escalável sem gestão de cluster;
- integração nativa com Cloud Storage e Pub/Sub;
- adequado a dados tabulares educacionais;
- viável para o volume do projeto no contexto acadêmico.

**Trade-off:** menor flexibilidade de processamento genérico (ex.: Spark amplo) em troca de simplicidade operacional e velocidade de entrega.

**Alternativas consideradas:** AWS (S3 + Athena/Redshift) e Azure (ADLS + Synapse). Descartadas para este MVP pela coesão GCS + BQ + Pub/Sub e pelo ambiente já disponível.

---

### D2. Arquitetura Medalhão (Bronze / Silver / Gold)

**Decisão:** separar explicitamente três camadas de responsabilidade.

| Camada | Responsabilidade | O que não faz |
|--------|------------------|---------------|
| Bronze | Preservar bruto e histórico de ingestão | Limpeza de negócio |
| Silver | Padronizar tipos, chaves e qualidade básica | Agregação analítica final |
| Gold | Entregar datasets prontos para análise | Guardar ruído de origem |

**Por quê:**
- facilita reprocessamento a partir do bruto;
- isola regras de limpeza das regras analíticas;
- deixa a Gold estável para consumo (dashboard, estatística, IA).

**Trade-off:** mais objetos e etapas para manter; ganho em governança e clareza.

---

### D3. Padrão Lake + Warehouse (não “um ou outro”)

**Decisão:**
- **GCS** como landing zone / data lake leve para arquivos brutos;
- **BigQuery** como data warehouse analítico.

**Por quê:**
- GCS é eficiente para armazenar bruto (CSV de microdados e metas);
- BigQuery é eficiente para transformação SQL, joins e consumo analítico;
- separa custo/armazenamento de bruto do custo/consulta analítica.

**Trade-off:** dois componentes para operar (storage + warehouse), em troca de melhor encaixe custo × performance.

---

### D4. Ingestão híbrida: batch + streaming

**Decisão:**
- **Batch** para bases históricas e periódicas (AEEB, Metas, Censo);
- **Streaming** (Pub/Sub) para simular atualizações near real-time de indicadores/metas.

**Por quê:**
- metas e microdados educacionais chegam em ciclos (não como fluxo contínuo de sensores);
- o challenge exige demonstrar capacidade híbrida;
- Pub/Sub + tabela `eventos_streaming` prova o padrão sem forçar streaming onde batch é o modelo natural.

**Trade-off:** o streaming do MVP é **simulado e controlado** (demo com eventos derivados da Gold), não um feed operacional 24/7. Isso é intencional: demonstra o padrão arquitetural com complexidade compatível ao prazo.

**Fluxo streaming implementado:**
1. `simulador_pubsub.py` publica eventos no tópico `alfabetizacao-eventos`
2. `consumidor_bq.py` consome a subscription e grava em `bronze_alfabetizacao.eventos_streaming`
3. tipos de evento: `atualizacao_indicador` e `atualizacao_meta`

---

### D5. Fontes de dados e papel de cada uma

**Decisão de fontes no MVP:**

| Fonte | Papel arquitetural |
|-------|--------------------|
| AEEB 2025 | Base principal do indicador de alfabetização |
| Metas e Resultados | Série de resultados e trajetória de metas até 2030 |
| Censo Escolar 2024 | Enriquecimento de contexto (rede, matrícula, infraestrutura) |
| Base dos Dados / datasets públicos BQ | Referência de schema e apoio conceitual |

**Por quê essa combinação:**
- AEEB e Metas cobrem diretamente o problema do Indicador Criança Alfabetizada;
- o Censo adiciona variáveis de estrutura escolar úteis para análise de desigualdade;
- a ingestão primária a partir de arquivos públicos locais + Python SDK garantiu materialidade no projeto GCP disponível.

**Trade-off / transparência:**  
o enunciado cita a Base dos Dados como fonte de referência do indicador. Neste MVP, a **carga operacional** foi feita com microdados e planilhas oficiais do INEP, usando o ecossistema público/BQ como referência. A narrativa do projeto trata isso como decisão pragmática de disponibilidade e reprodutibilidade no ambiente da equipe — não como desvio do problema de negócio.

---

### D6. Python SDK como canal oficial de interação com GCP

**Decisão:** scripts Python (`google-cloud-bigquery`, `storage`, `pubsub`) como interface principal; não depender do CLI `bq` para a pipeline.

**Por quê:**
- controle fino de encoding (`latin-1` / `UTF-8`) e delimitadores (`;` / `,`);
- no ambiente local, o CLI `bq` apresentou `Access Denied` mesmo em datasets públicos, enquanto o SDK funcionou;
- scripts versionáveis, testáveis e alinhados ao repositório.

**Trade-off:** menos “clique no console” e mais código para manter; ganho em reprodutibilidade.

---

### D7. Grão analítico: município (e UF), não aluno na Gold

**Decisão:** a Gold é centrada em **município** e **UF**.

**Por quê:**
- metas e acompanhamento de política pública ocorrem nesses grãos;
- `TS_MUNICIPIO` já oferece o indicador agregado (`pc_aluno_alfabetizado`);
- `TS_ALUNO` (~2,2M linhas) permanece disponível na Bronze/GCS, mas não é necessário para o MVP analítico.

**Trade-off:** perde-se granularidade aluno/escola na Gold atual; ganha-se foco, performance e simplicidade.

---

### D8. Estratégia de join entre AEEB, Metas e Censo

**Decisão:**
- AEEB filtrado em `id_tipo_rede = 3` (rede municipal);
- Metas filtradas em `tp_rede = 'MUNICIPAL'`;
- Censo agregado por `co_municipio` (escolas com anos iniciais do fundamental).

**Por quê:**
- a base de metas municipais está no recorte municipal;
- alinhar redes evita comparar recortes incompatíveis;
- o Censo entra como contexto, não como fonte do indicador.

**Resultado observado:**
- cobertura Gold ↔ Metas ≈ **99,3%**
- cobertura Gold ↔ Censo ≈ **99,98%**

**Trade-off:** municípios sem match completo ficam com campos nulos de meta ou contexto; isso é preferível a imputação artificial.

---

### D9. Silver: limpeza objetiva, sem “embelezar” o bruto

**Decisões de transformação Silver:**
- remover header duplicado das Metas;
- renomear/padronizar colunas e tipos;
- selecionar subset do Censo (em vez das 426 colunas brutas);
- manter chaves de negócio explícitas (`co_municipio`, `co_uf`, `co_entidade`).

**Por quê:** Silver deve ser reutilizável e auditável. Transformações de negócio pesadas (gap, ranking, consolidação multi-fonte) ficam na Gold.

---

### D10. Qualidade de dados como etapa versionada

**Decisão:** implementar `src/qualidade/validacoes.py` com checks executáveis sobre Silver/Gold e gerar evidência em `docs/evidencias/resultado_auditoria.md`.

**Cobertura:**
- nulos em chaves;
- duplicidade;
- ranges de percentual;
- consistência de joins;
- integridade referencial leve entre camadas;
- consistência do cálculo `gap_meta_2025`.

**Por quê:** qualidade é requisito explícito do challenge e precisa ser demonstrável, não apenas declarada.

**Resultado da execução de referência:** 27 PASS / 0 WARN / 0 FAIL.

---

### D11. Orquestração do MVP por scripts (sem Composer/Airflow)

**Decisão:** execução sequencial por scripts Python no repositório.

**Por quê:**
- prazo e escopo acadêmico;
- transparência total do fluxo no Git;
- suficiente para demonstrar a pipeline ponta a ponta.

**Trade-off:** sem agendamento, retry policy e SLA de produção. Aceitável no MVP; evolução natural seria Cloud Scheduler + Cloud Functions/Run ou Composer.

---

## 3. Trade-offs exigidos pelo challenge (síntese)

| Dimensão | Escolha | Alternativa | Motivo da escolha |
|----------|---------|-------------|-------------------|
| Batch vs Streaming | Híbrido | Só batch ou só streaming | Histórico periódico + eventos de atualização |
| Lake vs Warehouse | GCS + BigQuery | Apenas lake ou apenas warehouse | Bruto barato + consulta analítica eficiente |
| Cloud provider | GCP | AWS / Azure | Integração BQ + GCS + Pub/Sub no ambiente disponível |
| Grão Gold | Município/UF | Aluno | Alinhamento com metas e custo/complexidade do MVP |
| Orquestração | Scripts Python | Airflow/Composer | Entrega rápida e auditável no repositório |
| Qualidade | Checks versionados no BQ | Só validação manual | Rastreabilidade e evidência objetiva |

---

## 4. O que a arquitetura habilita

### Análises imediatas
- ranking de municípios por gap meta × resultado;
- evolução 2023 → 2025;
- cruzamento de desempenho com infraestrutura escolar e matrículas.

### Usos futuros de IA (sobre a Gold)
1. modelo de **propensão a não atingir meta**;
2. **clusters de vulnerabilidade educacional**;
3. sistema de **priorização de intervenção territorial**.

A Gold foi desenhada para ser a base dessas aplicações, sem acoplar ML ao MVP de engenharia.

---

## 5. Limitações conscientes

1. Streaming demonstrável, não operacional contínuo.  
2. Sem camada de monitoramento avançado (alertas/SLA) neste momento.  
3. Sem particionamento/clustering fino exaustivo em todas as tabelas.  
4. FinOps será detalhado em discussão/documentação específica (fora do escopo deste documento por enquanto).  
5. Diagrama visual final e prints de console complementam este texto em `docs/diagramas/` e `docs/evidencias/`.

---

## 6. Mapa rápido: decisão → artefato no repositório

| Decisão | Artefato |
|---------|----------|
| Infra GCP | `src/infra/` |
| Batch Bronze | `src/ingestao/` |
| Silver | `src/transformacao/silver_*.py` |
| Gold | `src/transformacao/gold_indicadores.py` |
| Qualidade | `src/qualidade/validacoes.py` |
| Streaming | `src/streaming/` |
| Evidência de qualidade | `docs/evidencias/resultado_auditoria.md` |
| Visão executiva | `README.md` |

---

## 7. Conclusão

A arquitetura escolhida privilegia:

- **aderência ao problema educacional** (indicador + metas + contexto);
- **clareza medalhão**;
- **hibridismo batch/streaming demonstrável**;
- **reprodutibilidade via código**;
- **camada Gold consumível por análise e IA**.

Os trade-offs foram aceitos de forma explícita para maximizar valor entregue no prazo do Tech Challenge, sem perder solidez conceitual de engenharia de dados.
