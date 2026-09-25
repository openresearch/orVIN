#!/bin/sh
set -eu
ORVIN_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ORVIN_PYTHON=${ORVIN_PYTHON:-python3}
if ! command -v "$ORVIN_PYTHON" >/dev/null 2>&1; then
    echo "Orvin requires Python 3.10+. Install Python or set ORVIN_PYTHON to its executable." >&2
    exit 1
fi
if ! "$ORVIN_PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then
    echo "Orvin requires Python 3.10+. No JDK or package installation is needed." >&2
    exit 1
fi
PYTHONPATH="$ORVIN_ROOT/libs/python${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONPATH
cd "$ORVIN_ROOT"
exec "$ORVIN_PYTHON" -m orvin "$@"
