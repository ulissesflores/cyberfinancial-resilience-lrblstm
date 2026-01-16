# Cyber-Financial Resilience via Little’s Law + Bayesian LSTM (LR-BLSTM)

Repositório científico para experimentos reprodutíveis em resiliência ciberfinanceira,
integrando invariantes de fluxo (Lei de Little) e Deep Learning Bayesiano (LSTM).

🔗 Artigo (ID imutável):  
https://ulissesflores.com/research/2025-little-law-resilience

---

## Objetivo Científico

Este projeto investiga se:
1. Invariantes de fluxo (Lei de Little) podem ser usados como **restrições estruturais** em modelos neurais;
2. Inferência Bayesiana melhora **calibração e decisão sob incerteza Knightiana**;
3. Um loop preditivo de controle de fluxo aumenta **resiliência operacional** sob estresse.

---

## Contrato de Reprodutibilidade (Não negociável)

Toda execução **DEVE** gerar um diretório `runs/<run_id>/` contendo:
- `manifest.json`
- `checksums.sha256`
- `data.parquet` (ou shards)
- `figures/`
- `metrics.json` (quando aplicável)

Execuções sem manifest são **cientificamente inválidas**.

---

## Estrutura do Projeto

Veja:
- `docs/data_rationale.md` — justificativa causal dos dados
- `docs/reproducibility.md` — como reproduzir
- `schema/manifest_schema.md` — contrato de execução
- `scripts/` — instrumentação e experimentos
- `notebooks/` — notebooks reprodutíveis (Colab)

---

## Licença
MIT

## Como Citar
Veja `CITATION.cff` ou o DOI no Zenodo (após o primeiro release).
