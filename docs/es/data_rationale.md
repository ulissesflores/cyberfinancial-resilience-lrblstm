# Justificación de Datos (Fase 1) — Proxies Públicos para Resiliencia Ciberfinanciera

## Premisa
El sistema bajo análisis es un **sistema ciberfinanciero sociotécnico** cuyo comportamiento emergente es parcialmente observable por **métricas públicas** de mercado (precio y negociaciones). La Ley de Little (L = λW) se trata como **invariante estructural de flujo**, pero **no es directamente observable** a partir de datos públicos.

## Evidencia
1. **Mercados cripto** exhiben colas pesadas, regímenes y no estacionariedad en múltiples escalas.
2. Datos públicos disponibles de forma reproducible:
   - OHLCV en 1 minuto (proxy de régimen de precio)
   - Trades (proxy de intensidad/llegadas y *burstiness*)
3. La microestructura real (order book profundo, colas de ejecución internas, telemetría de OMS/infraestructura) no está expuesta integralmente por APIs públicas.

## Conclusión Crítica
En la Fase 1, adoptamos **proxies observacionales** para construir una base empírica auditable:
- **Regime proxy:** volatilidad realizada (RV) y drawdown logarítmico.
- **Arrival proxy:** distribución de inter-arrival de trades (indicativo de cola y autocorrelación).
- **Intensity proxy (λ(t)):** trades/min como proxy de tasa de llegada.

No hay alegación de causalidad ni de medición directa de (L, λ, W) de colas internas de ejecución. Estos componentes serán tratados en fases posteriores mediante **telemetría operacional** o simulación calibrada.