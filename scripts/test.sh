#!/bin/sh
set -eu
PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONPATH="$PROJECT_DIR/src"
cd "$PROJECT_DIR"
exec python3 -m unittest discover -s tests -v "$@"

