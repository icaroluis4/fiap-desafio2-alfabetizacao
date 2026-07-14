# FIAP Desafio 2 — Alfabetização no Brasil

Pipeline de dados para análise do indicador de alfabetização no Brasil, construída sobre arquitetura medalhão (Bronze / Silver / Gold) no GCP.

## Contexto

Este projeto integra dados públicos do INEP (AEEB 2025 e Censo Escolar 2024) para gerar uma camada analítica confiável sobre a alfabetização municipal e estadual no Brasil.

## Arquitetura

- **Bronze**: dados brutos armazenados no Cloud Storage e carregados no BigQuery.
- **Silver**: limpeza, padronização e integração entre fontes.
- **Gold**: agregações analíticas (indicadores por município, metas vs resultados, evolução temporal).

## Estrutura do Repositório

```
├── docs/               # Documentação, evidências e diagramas
├── src/                # Código-fonte da pipeline
│   ├── infra/          # Provisionamento de infraestrutura GCP
│   ├── ingestao/       # Ingestão batch → Bronze
│   ├── transformacao/  # Silver e Gold
│   ├── qualidade/      # Validações e monitoramento
│   └── streaming/      # Simulação de ingestão em tempo real
├── sql/                # SQLs versionados por camada
├── tests/              # Testes automatizados
└── notebooks/          # Análises exploratórias
```

## Requisitos

- Python 3.11+
- Conta GCP com projeto e billing ativados
- Autenticação via Application Default Credentials (`gcloud auth application-default login`)

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

*(Em construção — serão adicionados comandos de execução da pipeline.)*

---

> Projeto desenvolvido para o Tech Challenge da Fase 2 da pós-graduação em Arquitetura de Big Data — FIAP.
