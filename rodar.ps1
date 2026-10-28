# Cria o ambiente (uma vez), roda o pipeline inteiro e os testes.
#   .\rodar.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".venv")) { python -m venv .venv }
.\.venv\Scripts\python -m pip install -q -r requirements.txt
$env:PYTHONUTF8 = "1"
.\.venv\Scripts\python -m src.pipeline
.\.venv\Scripts\python -m unittest -v
