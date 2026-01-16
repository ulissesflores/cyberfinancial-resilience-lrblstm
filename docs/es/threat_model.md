# Modelo de Amenazas y Amenazas a la Validez (Fase 1)

## 1) Amenazas a la validez interna (inferencia)
- **Correlación espuria:** los proxies pueden correlacionar por régimen común, no por causalidad.
- **No estacionariedad / cambios de régimen:** los patrones cambian; los resultados dependen de la ventana temporal seleccionada.
- **Muestreo/truncamiento:** los trades pueden estar limitados por API o por el parámetro `max_trades`.
- **Alineación temporal:** desalineaciones entre OHLCV y trades pueden producir artefactos si la agregación no es consistente.

## 2) Amenazas a la validez externa (generalización)
- **Específico del Exchange:** Binance no representa todo el ecosistema.
- **Específico del Instrumento:** BTC/USDT puede diferir de altcoins.
- **Cambios en la microestructura de mercado:** cambios de tarifas, motor de emparejamiento, liquidez.

## 3) Amenazas operacionales (reproducibilidad)
- Dependencia de API pública (disponibilidad, rate limits).
- Dependencias de biblioteca (ej.: `pyarrow`) varían por plataforma.
- Zona horaria/locale: mitigado por el uso de UTC end-to-end.

## 4) Amenazas adversarias (cuando avancemos a la Fase 2)
- **Envenenamiento de datos (Data poisoning):** inyección de patrones vía wash trading (limitado en la Fase 1, pero posible).
- **Concept drift adversarial:** cambios deliberados en la microestructura pueden “romper” modelos.
- **Efectos de Goodhart:** usar predicción para controlar ejecución puede retroalimentar el sistema.

## 5) Mitigaciones (Fase 1)
- Manifiesto + checksums SHA-256.
- Logs y `run_id` inmutables.
- Declaración explícita de proxies (sin afirmaciones exageradas).
- Resumen de Datos + esquemas formales.

## 6) Criterios de falsación (Fase 1)
- Si las distribuciones de inter-arrival no exhiben cola pesada o clustering, la hipótesis de *burstiness* relevante para la resiliencia debe ser revisada.
- Si λ(t) no varía significativamente, la utilidad del proxy de intensidad puede ser marginal para la ventana analizada.