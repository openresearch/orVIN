#!/bin/sh
set -eu
ORVIN_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$ORVIN_ROOT/tools/run-python.sh" hsntsn "$@"
