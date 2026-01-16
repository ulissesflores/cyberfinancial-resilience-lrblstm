# Tarjeta de Modelo — LR-BLSTM (Fase 1 → Fase 2)

## Modelo (visión general)
**LR-BLSTM** (Little-Regularized Bayesian LSTM) es un plan de modelado que combina:
- invariantes/restricciones inspirados en la Ley de Little,
- modelado secuencial (LSTM),
- calibración de incertidumbre (Bayesian deep learning).

## Estado actual (Fase 1)
**No hay entrenamiento de modelo todavía.** La Fase 1 produce:
- dataset público curado (OHLCV + trades),
- figuras y diagnósticos de regímenes,
- métricas de llegada/intensidad.

## Objetivo de predicción (Fase 2)
Inferir un estado latente de “resiliencia” y/o inestabilidad (ej.: probabilidad de régimen de estrés), con incertidumbre calibrada.

## Entradas (Observables de Fase 1)
- OHLCV 1m: open, high, low, close, volume
- Trades: timestamps (ms), price, amount (cuando disponible), side (cuando disponible)

## Salidas (Fase 1)
- Figuras EDA (PNG)
- Tablas de Resumen de Datos (MD/CSV/JSON)
- Manifiesto + checksums

## Métricas futuras (Fase 2)
- Error de predicción: MAE/RMSE
- Robustez y estrés: splits por regímenes
- Calibración: ECE/CRPS
- Métricas de resiliencia: tiempo de recuperación (proxy), supervivencia a drawdown, degradación de throughput (proxy)

## Limitaciones (Fase 1)
- Los proxies públicos no miden directamente L, λ, W de colas internas.
- La API pública puede imponer límites y truncamientos.
- La no estacionariedad implica riesgo de generalización.

## Responsable
Carlos Ulisses Flores — Codex Hash Ltda. (Brasil)