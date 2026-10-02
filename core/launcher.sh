#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python3 >/dev/null 2>&1; then
    PY=python3
elif command -v python >/dev/null 2>&1; then
    PY=python
else
    echo "Python 3.10+ was not found on PATH. Install it from https://python.org and try again." >&2
    exit 1
fi

"$PY" "$DIR/launcher.py" "$@"
