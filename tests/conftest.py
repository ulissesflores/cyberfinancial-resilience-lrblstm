"""Pytest configuration: make the ``scripts/`` package importable.

The scripts use flat imports (``from hash_utils import ...``), matching how they
are invoked from the repository root. Inserting ``scripts/`` on ``sys.path``
lets the test suite import them directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
