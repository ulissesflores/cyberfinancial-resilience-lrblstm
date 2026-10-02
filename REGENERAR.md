# REGENERAR — cyberfinancial-resilience-lrblstm

Este repositório não versiona o ambiente Python (`.venv`) nem caches de execução. Código, dados de configuração e testes seguem versionados normalmente em `scripts/` e `tests/`. Esta nota documenta como recriar as subárvores abaixo a partir do zero.

## O que não é versionado

| pasta | arquivos | GiB (soma dos bytes) |
| --- | --- | --- |
| `.venv` | 26581 | 0.782 |
| caches (`__pycache__`, `.pytest_cache`, `.ruff_cache`; 4 pastas) | 21 | 0.000 (0.1 MiB) |
| **total** | **26602** | **0.782** |

Base do ambiente: Python 3.11.15 (uv, cpython-3.11), 50 pacotes no freeze (torch 2.12.0, numpy 2.1.3, pandas 2.2.3, ccxt 4.4.92...).

## Como recriar

```bash
cd "$(git rev-parse --show-toplevel)"   # raiz do repositório, de onde quer que você esteja dentro dele
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.lock.txt
# alternativa sem uv:
#   python3.11 -m venv .venv && .venv/bin/pip install -r requirements.lock.txt
```

Fonte da receita: `requirements.lock.txt` (freeze completo, 50 pacotes; `uv pip install --dry-run` resolveu tudo). O `requirements.txt` versionado tem só 7 pins de topo (ccxt, pandas, numpy, pyarrow, tqdm, python-dateutil, matplotlib) e NÃO recria o venv completo (faltam, por exemplo, torch, scipy e pytest): use o `.lock.txt`.

Data: 2026-09-29.
