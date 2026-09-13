#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONPATH="$PROJECT_DIR/src"
exec python3 -m tb_ai_lab build "$@"

