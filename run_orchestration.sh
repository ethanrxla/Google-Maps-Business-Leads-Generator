#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="/home/ethan/projects/Thei_Molt/leads/.venv/bin/python"
PIP_BIN="/home/ethan/projects/Thei_Molt/leads/.venv/bin/pip"
ROOT_DIR="/home/ethan/projects/Thei_Molt/leads"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "error: required interpreter not found: $PYTHON_BIN" >&2
  exit 1
fi

cd "$ROOT_DIR"

# Dependency check first; install only missing packages through venv pip.
MISSING_LINES="$($PYTHON_BIN - <<'PY'
import importlib.util
from pathlib import Path

req = Path('requirements.txt')
module_map = {
    'python-dotenv': 'dotenv',
    'beautifulsoup4': 'bs4',
    'pyyaml': 'yaml',
}
missing = []
for raw in req.read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#'):
        continue
    name = line.split('==')[0].split('>=')[0].split('[')[0].strip()
    mod = module_map.get(name.lower(), name.replace('-', '_'))
    if importlib.util.find_spec(mod) is None:
        missing.append(line)
print('\n'.join(missing))
PY
)"

if [[ -n "${MISSING_LINES// }" ]]; then
  echo "Installing missing deps (venv pip only):"
  echo "$MISSING_LINES"
  while IFS= read -r dep; do
    [[ -z "$dep" ]] && continue
    timeout 300 "$PIP_BIN" install --disable-pip-version-check "$dep"
  done <<< "$MISSING_LINES"
else
  echo "Dependencies already satisfied."
fi

# Conservative wall timeout. Override with ORCH_WALL_TIMEOUT if needed.
WALL_TIMEOUT="${ORCH_WALL_TIMEOUT:-1800}"
exec timeout --preserve-status "$WALL_TIMEOUT" \
  "$PYTHON_BIN" -m leadgen.orchestrate_full_run "$@"
