#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
(cd "$ROOT_DIR/services/atlas-engine" && PYTHONPATH=src pytest tests -v)
(cd "$ROOT_DIR/services/delta-engine" && PYTHONPATH=src pytest tests -v)
(cd "$ROOT_DIR/services/atlas-api" && PYTHONPATH=src:../atlas-engine/src:../delta-engine/src pytest tests -v)
