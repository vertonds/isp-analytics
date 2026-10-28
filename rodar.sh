#!/usr/bin/env bash
# Cria o ambiente (uma vez), roda o pipeline inteiro e os testes. Equivalente Linux/macOS do rodar.ps1.
#   ./rodar.sh
set -euo pipefail
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/python -m pip install -q -r requirements.txt
export PYTHONUTF8=1
.venv/bin/python -m src.pipeline
.venv/bin/python -m unittest -v
