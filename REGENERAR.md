# REGENERAR — cyberfinancial-resilience-lrblstm

Poda do projeto DISCO em 2026-09-29 (aprovada pelo Ulisses às 22h30): saem as subárvores regeneráveis abaixo e mais nada. Código, dados, `.env` e `.git` NÃO são tocados.

> [!NOTE]
> A remoção é feita por um executor separado, depois desta nota. Se as pastas listadas ainda existirem, a poda ainda não rodou. Lista exata dos arquivos: `/Users/ulissesflores/m4/docs/projects/disco-tmp-2026-09-28/evidencia/lote-2026-09-29/poda-cyberfinancial-resilience-lrblstm-apagar.tsv`.

## O que sai

| pasta | arquivos | GiB (soma dos bytes) |
| --- | --- | --- |
| `.venv` | 26581 | 0.782 |
| caches (`__pycache__`, `.pytest_cache`, `.ruff_cache`; 4 pastas) | 21 | 0.000 (0.1 MiB) |
| **total** | **26602** | **0.782** |

Base do ambiente: Python 3.11.15 (uv, cpython-3.11), 50 pacotes no freeze (torch 2.12.0, numpy 2.1.3, pandas 2.2.3, ccxt 4.4.92...).

## Como recriar

```bash
cd /Users/ulissesflores/Developer/cyberfinancial-resilience-lrblstm
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.lock.txt
# alternativa sem uv:
#   python3.11 -m venv .venv && .venv/bin/pip install -r requirements.lock.txt
```

Fonte da receita: `requirements.lock.txt` (freeze feito em 2026-09-29 antes da poda, 50 pacotes; `uv pip install --dry-run` resolveu tudo). O `requirements.txt` versionado tem só 7 pins de topo (ccxt, pandas, numpy, pyarrow, tqdm, python-dateutil, matplotlib) e NÃO recria o venv completo (faltam, por exemplo, torch, scipy e pytest): use o `.lock.txt`.

## Avisos

> [!WARNING]
> **COMMITAR ANTES.** Os 7 arquivos não versionados deste repo (`scripts/controller.py`, `scripts/models.py`, `scripts/simulate.py`, `scripts/train_lr_blstm.py`, `scripts/figures_ablation.py`, `scripts/metrics.py` e `tests/`) são TODO o código-fonte do projeto e nunca foram commitados. A poda mexe só em `.venv` e caches, e não toca neles, mas nem `git clone` nem tar do repo protegem esse trabalho enquanto não houver commit. Commit e push dependem de decisão do Ulisses. Este `REGENERAR.md` e o `requirements.lock.txt` também são arquivos novos não versionados.

Data: 2026-09-29.
