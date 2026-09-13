#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONPATH="$PROJECT_DIR/src"
if [ "$#" -eq 0 ]; then
  set -- evaluate --calibration
fi
exec python3 -m tb_ai_lab "$@"

