# Declaração de Reprodutibilidade

Este documento define o contrato de reprodutibilidade para o projeto **Cyber-Financial Resilience via Little’s Law and Bayesian LSTM**.

O objetivo é garantir que todos os resultados, figuras e tabelas reportados possam ser regenerados independentemente a partir de dados públicos brutos, sujeitos a limitações claramente declaradas.

---

## Escopo

Esta declaração de reprodutibilidade aplica-se à **Fase 1** do projeto, que inclui:
- Coleta de dados públicos (OHLCV e trades).
- Análise Exploratória de Dados (EDA) com grau de auditoria.
- Tabelas de resumo de dados utilizadas nas seções de Métodos/Dados do artigo associado.

Nenhuma alegação de inferência causal ou observabilidade em nível de infraestrutura é feita nesta fase.

---

## Unidades Reprodutíveis

A unidade fundamental de reprodutibilidade é uma **run** (execução), identificada por um `run_id` único.

Cada run contém:
- Artefatos de dados brutos (arquivos Parquet).
- Figuras e tabelas geradas.
- Logs de execução.
- Um `manifest.json` legível por máquina.
- Checksums criptográficos (`checksums.sha256`).

Uma vez criada, uma run é tratada como **imutável**.

---

## Componentes Determinísticos

Os seguintes componentes são determinísticos, condicionados a entradas idênticas:
- Engenharia de features e computações estatísticas.
- Código de geração de figuras.
- Tabelas de resumo de dados.
- Geração de manifesto e checksum.

Dados os mesmos arquivos de entrada, esses componentes produzirão saídas idênticas bit a bit.

---

## Aspectos Não-Reprodutíveis Conhecidos (Deriva de API)

Apesar das melhores práticas, a reprodutibilidade total bit a bit não pode ser garantida para todos os estágios devido a dependências externas:

1. **APIs de Exchanges Públicas**
   - Endpoints de OHLCV e trades podem alterar a disponibilidade histórica ao longo do tempo.
   - Limites de taxa (rate limits), comportamento de paginação ou políticas de backfill podem evoluir.
2. **Evolução do Mercado**
   - Mercados cripto são não-estacionários; reexecutar a coleta de dados em uma data posterior produz amostras diferentes.
3. **Restrições de Endpoint**
   - Endpoints de trades frequentemente impõem limites implícitos ou explícitos (ex.: máximo de trades por requisição ou janelas de lookback).

Como resultado, a reprodutibilidade estrita requer o **congelamento de datasets** (ex.: via releases no Zenodo) em vez de reconsultar APIs vivas.

---

## Procedimento de Verificação

Para verificar uma run publicada:

1. Obtenha o diretório da run arquivada (ex.: via Zenodo ou assets de release no GitHub).
2. Recalcule os checksums:

```bash
shasum -a 256 -c checksums.sha256
```

3. Confirme se todos os artefatos validam sem incompatibilidade.

Se os checksums corresponderem, a run é considerada totalmente reproduzida.

---

## Fluxo de Trabalho de Reprodução (Fase 1)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/collect_data.py --run_id <RUN_ID> [options]
python scripts/eda_generate_figures.py --run_id <RUN_ID>
python scripts/data_summary.py --run_id <RUN_ID>
```

---

## Classificação de Reprodutibilidade

Seguindo a terminologia comum:
- **Reprodutibilidade forte:** alcançada quando datasets e artefatos arquivados são reutilizados.
- **Reprodutibilidade fraca:** alcançada quando APIs vivas são reconsultadas sob condições similares.

Este projeto visa explicitamente a **reprodutibilidade forte** para resultados publicados.

---

## Autoria e Responsabilidade

Design e implementação de reprodutibilidade:
- **Carlos Ulisses Flores** — Pesquisador Independente; CTO & Chief Researcher, Codex Hash Ltda.