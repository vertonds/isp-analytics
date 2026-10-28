"""Orquestra o pipeline inteiro: Stage → SOR → SOT → SPEC → portas → relatório.

    python -m src.pipeline            # tudo
    python -m src.pipeline --sem-gerar   # reaproveita o Stage que já existe
"""
from __future__ import annotations

import sys
import time

from . import camadas, carregar_sor, gerar_dados, portas, relatorio
from .controle import conectar, registrar


def _passo(nome: str, fn, *a):
    t0 = time.perf_counter()
    r = fn(*a)
    print(f"[{time.perf_counter() - t0:6.1f}s] {nome}: {r}")
    return r


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    con = conectar()
    if "--sem-gerar" not in argv:
        _passo("stage (gerar)", gerar_dados.gerar)
    _passo("sor", carregar_sor.carregar, con)
    _passo("sot", camadas.construir_sot, con)
    _passo("spec", camadas.construir_spec, con)
    with registrar(con, "portas") as d:
        d.update(_passo("portas", portas.conferir, con))
    _passo("relatorio", relatorio.gerar, con)
    print("pipeline concluído — portas OK, relatório em docs/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
