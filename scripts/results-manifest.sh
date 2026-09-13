#!/bin/sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
MANIFEST="$PROJECT_DIR/RESULTS_MANIFEST.sha256"

cd "$PROJECT_DIR"

artifact_paths() {
  find data/generated reports -type f \
    ! -name '*-checkpoint.json' \
    ! -name '*-plan.json' \
    ! -name '*.tmp' \
    -print0 | LC_ALL=C sort -z
}

case "${1:-verify}" in
  update)
    temporary_manifest=$(mktemp "$PROJECT_DIR/.results-manifest.XXXXXX")
    trap 'rm -f "$temporary_manifest"' EXIT HUP INT TERM
    artifact_paths | xargs -0 -r sha256sum > "$temporary_manifest"
    mv "$temporary_manifest" "$MANIFEST"
    trap - EXIT HUP INT TERM
    ;;
  verify)
    test -f "$MANIFEST"
    sha256sum --check --strict "$MANIFEST"
    ;;
  *)
    echo "usage: $0 [verify|update]" >&2
    exit 2
    ;;
esac
