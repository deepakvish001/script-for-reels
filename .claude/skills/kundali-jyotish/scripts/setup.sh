#!/usr/bin/env bash
# Finds or creates a Python that can `import swisseph` and prints its path.
# Usage:  PY=$(bash scripts/setup.sh) && $PY scripts/jyotish.py chart ...
# Order: existing python3 -> cached venv -> pip install -> new venv.
VENV="${JYOTISH_VENV:-$HOME/.cache/jyotish-venv}"
ok() { "$1" -c "import swisseph" >/dev/null 2>&1; }
if command -v python3 >/dev/null && ok python3; then command -v python3; exit 0; fi
if [ -x "$VENV/bin/python" ] && ok "$VENV/bin/python"; then echo "$VENV/bin/python"; exit 0; fi
python3 -m pip install --quiet --user pyswisseph >/dev/null 2>&1 && ok python3 && { command -v python3; exit 0; }
python3 -m venv "$VENV" >/dev/null 2>&1 && "$VENV/bin/pip" install --quiet pyswisseph >/dev/null 2>&1 \
  && ok "$VENV/bin/python" && { echo "$VENV/bin/python"; exit 0; }
echo "FAILED: could not install pyswisseph (no network/compiler?). Fall back to the report's own" \
     "tables; the dasha command still works with --moon-lon (plain python3)." >&2
exit 1
