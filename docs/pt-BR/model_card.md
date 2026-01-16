# Model Card — LR-BLSTM (Fase 1 → Fase 2)

## Modelo (visão geral)
**LR-BLSTM** (Little-Regularized Bayesian LSTM) é um plano de modelagem que combina:
- invariantes/restrições inspirados na Lei de Little,
- modelagem sequencial (LSTM),
- calibração de incerteza (Bayesian deep learning).

## Estado atual (Fase 1)
**Não há treinamento de modelo ainda.** A Fase 1 produz:
- dataset público curado (OHLCV + trades),
- figuras e diagnósticos de regimes,
- métricas de chegada/intensidade.

## Objetivo de previsão (Fase 2)
Inferir um estado latente de “resiliência” e/ou instabilidade (ex.: probabilidade de regime de estresse), com incerteza calibrada.

## Entradas (Observáveis da Fase 1)
- OHLCV 1m: open, high, low, close, volume
- Trades: timestamps (ms), price, amount (quando disponível), side (quando disponível)

## Saídas (Fase 1)
- Figuras EDA (PNG)
- Tabelas de Resumo de Dados (MD/CSV/JSON)
- Manifesto + checksums

## Métricas futuras (Fase 2)
- Erro de previsão: MAE/RMSE
- Robustez e estresse: splits por regimes
- Calibração: ECE/CRPS
- Métricas de resiliência: tempo de recuperação (proxy), sobrevivência a drawdown, degradação de throughput (proxy)

## Limitações (Fase 1)
- Proxies públicos não medem diretamente L, λ, W de filas internas.
- API pública pode impor limites e truncamentos.
- Não-estacionaridade implica risco de generalização.

## Responsável
Carlos Ulisses Flores — Codex Hash Ltda. (Brasil)