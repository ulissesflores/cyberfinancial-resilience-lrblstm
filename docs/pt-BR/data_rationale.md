# Justificativa de Dados (Fase 1) — Proxies Públicos para Resiliência Ciberfinanceira

## Premissa
O sistema sob análise é um **sistema ciberfinanceiro socio-técnico** cujo comportamento emergente é parcialmente observável por **métricas públicas** de mercado (preço e negociações). A Lei de Little (L = λW) é tratada como **invariante estrutural de fluxo**, mas **não é diretamente observável** a partir de dados públicos.

## Evidência
1. **Mercados cripto** exibem caudas pesadas, regimes e não-estacionaridade em múltiplas escalas.
2. Dados públicos disponíveis de forma reprodutível:
   - OHLCV em 1 minuto (proxy de regime de preço)
   - Trades (proxy de intensidade/chegadas e *burstiness*)
3. A microestrutura real (order book profundo, filas de execução internas, telemetria de OMS/infraestrutura) não é exposta integralmente por APIs públicas.

## Conclusão Crítica
Na Fase 1, adotamos **proxies observacionais** para construir uma base empírica auditável:
- **Regime proxy:** volatilidade realizada (RV) e drawdown logarítmico.
- **Arrival proxy:** distribuição de inter-arrival de trades (indicativo de cauda e autocorrelação).
- **Intensity proxy (λ(t)):** trades/min como proxy de taxa de chegada.

Não há alegação de causalidade nem de mensuração direta de (L, λ, W) de filas internas de execução. Esses componentes serão tratados em fases posteriores mediante **telemetria operacional** ou simulação calibrada.