#!/usr/bin/env bash
set -euo pipefail
ROOT=${1:-bautt-sigma}
mkdir -p "$ROOT"/{apps,services,packages,docs,infra,scripts}
echo "Scaffold base criado em $ROOT"
