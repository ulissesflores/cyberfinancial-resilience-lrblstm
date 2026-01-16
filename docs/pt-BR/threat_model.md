# Modelo de Ameaças e Ameaças à Validade (Fase 1)

## 1) Ameaças à validade interna (inferência)
- **Correlação espúria:** proxies podem correlacionar por regime comum, não por causalidade.
- **Não-estacionaridade / mudanças de regime:** padrões mudam; resultados dependem da janela temporal selecionada.
- **Amostragem/truncamento:** trades podem ser limitados por API ou pelo parâmetro `max_trades`.
- **Alinhamento temporal:** desalinhamentos entre OHLCV e trades podem produzir artefatos se a agregação não for consistente.

## 2) Ameaças à validade externa (generalização)
- **Específico da Exchange:** Binance não representa todo o ecossistema.
- **Específico do Instrumento:** BTC/USDT pode diferir de altcoins.
- **Mudanças na microestrutura de mercado:** alterações de taxas, matching engine, liquidez.

## 3) Ameaças operacionais (reprodutibilidade)
- Dependência de API pública (disponibilidade, rate limits).
- Dependências de biblioteca (ex.: `pyarrow`) variam por plataforma.
- Fuso horário/locale: mitigado pelo uso de UTC end-to-end.

## 4) Ameaças adversariais (quando avançarmos para a Fase 2)
- **Envenenamento de dados (Data poisoning):** injeção de padrões via wash trading (limitado na Fase 1, mas possível).
- **Concept drift adversarial:** mudanças deliberadas na microestrutura podem “quebrar” modelos.
- **Efeitos de Goodhart:** usar previsão para controlar execução pode retroalimentar o sistema.

## 5) Mitigações (Fase 1)
- Manifesto + checksums SHA-256.
- Logs e `run_id` imutáveis.
- Declaração explícita de proxies (sem alegações exageradas).
- Resumo de Dados + schemas formais.

## 6) Critérios de falsificação (Fase 1)
- Se as distribuições de inter-arrival não exibirem cauda pesada ou clustering, a hipótese de *burstiness* relevante para resiliência deve ser revista.
- Se λ(t) não variar significativamente, a utilidade do proxy de intensidade pode ser marginal para a janela analisada.