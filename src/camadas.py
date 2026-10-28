"""Etapas 2 e 3 — SOR → SOT (regras de negócio) e SOT → SPEC (agregados prontos para consumo).

As duas camadas são SÓ SQL: os arquivos de `sql/02_sor_sot/` e `sql/03_sot_spec/` rodam em ordem alfabética.
O Python só substitui os parâmetros de data (`__REF__`, `__INICIO__`) e registra a execução.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from . import config as C
from .controle import conectar, registrar


def _preparar(sql: str) -> str:
    return sql.replace("__REF__", C.DATA_REFERENCIA.isoformat()).replace("__INICIO__", C.INICIO_PERIODO.isoformat())


def executar_pasta(con: sqlite3.Connection, pasta: Path) -> list[str]:
    arquivos = sorted(pasta.glob("*.sql"))
    for f in arquivos:
        con.executescript(_preparar(f.read_text(encoding="utf-8")))
    con.commit()
    return [f.name for f in arquivos]


def construir_sot(con: sqlite3.Connection | None = None) -> list[str]:
    con = con or conectar()
    with registrar(con, "construir_sot") as d:
        d["arquivos"] = executar_pasta(con, C.SQL / "02_sor_sot")
    return d["arquivos"]


def construir_spec(con: sqlite3.Connection | None = None) -> list[str]:
    con = con or conectar()
    with registrar(con, "construir_spec") as d:
        d["arquivos"] = executar_pasta(con, C.SQL / "03_sot_spec")
    return d["arquivos"]


if __name__ == "__main__":
    c = conectar()
    print("SOT:", construir_sot(c))
    print("SPEC:", construir_spec(c))
