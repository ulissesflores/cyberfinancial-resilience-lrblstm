# Declaración de Reproducibilidad

Este documento define el contrato de reproducibilidad para el proyecto **Cyber-Financial Resilience via Little’s Law and Bayesian LSTM**.

El objetivo es asegurar que todos los resultados, figuras y tablas reportados puedan ser regenerados independientemente a partir de datos públicos brutos, sujetos a limitaciones claramente establecidas.

---

## Alcance

Esta declaración de reproducibilidad se aplica a la **Fase 1** del proyecto, que incluye:
- Recolección de datos públicos (OHLCV y trades).
- Análisis Exploratorio de Datos (EDA) con grado de auditoría.
- Tablas de resumen de datos utilizadas en las secciones de Métodos/Datos del artículo asociado.

No se hacen afirmaciones de inferencia causal u observabilidad a nivel de infraestructura en esta fase.

---

## Unidades Reproducibles

La unidad fundamental de reproducibilidad es una **run** (ejecución), identificada por un `run_id` único.

Cada run contiene:
- Artefactos de datos brutos (archivos Parquet).
- Figuras y tablas generadas.
- Logs de ejecución.
- Un `manifest.json` legible por máquina.
- Checksums criptográficos (`checksums.sha256`).

Una vez creada, una run se trata como **inmutable**.

---

## Componentes Determinísticos

Los siguientes componentes son determinísticos, condicionados a entradas idénticas:
- Ingeniería de características y computaciones estadísticas.
- Código de generación de figuras.
- Tablas de resumen de datos.
- Generación de manifiesto y checksum.

Dados los mismos archivos de entrada, estos componentes producirán salidas idénticas bit a bit.

---

## Aspectos No Reproducibles Conocidos (Deriva de API)

A pesar de las mejores prácticas, la reproducibilidad total bit a bit no puede garantizarse para todas las etapas debido a dependencias externas:

1. **APIs de Exchanges Públicos**
   - Los endpoints de OHLCV y trades pueden cambiar la disponibilidad histórica con el tiempo.
   - Los límites de tasa (rate limits), el comportamiento de paginación o las políticas de backfill pueden evolucionar.
2. **Evolución del Mercado**
   - Los mercados cripto son no estacionarios; reejecutar la recolección de datos en una fecha posterior produce muestras diferentes.
3. **Restricciones de Endpoint**
   - Los endpoints de trades a menudo imponen límites implícitos o explícitos (ej.: máximo de trades por solicitud o ventanas de lookback).

Como resultado, la reproducibilidad estricta requiere **congelar datasets** (ej.: vía releases en Zenodo) en lugar de reconsultar APIs vivas.

---

## Procedimiento de Verificación

Para verificar una run publicada:

1. Obtenga el directorio de la run archivada (ej.: vía Zenodo o assets de release en GitHub).
2. Recalcule los checksums:

```bash
shasum -a 256 -c checksums.sha256
```

3. Confirme que todos los artefactos se validan sin discrepancias.

Si las sumas de comprobación coinciden, la ejecución se considera totalmente reproducida.

---

## Reproduction Workflow (Phase 1)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/collect_data.py --run_id <RUN_ID> [options]
python scripts/eda_generate_figures.py --run_id <RUN_ID>
python scripts/data_summary.py --run_id <RUN_ID>
```

---

## Reproducibility Classification

Following common terminology:
- **Strong reproducibility:** achieved when archived datasets and artifacts are reused.
- **Weak reproducibility:** achieved when live APIs are re-queried under similar conditions.

This project explicitly targets **strong reproducibility** for published results.

---

## Authorship and Responsibility

Reproducibility design and implementation:
- **Carlos Ulisses Flores** — Independent Researcher; CTO & Chief Researcher, Codex Hash Ltda.
