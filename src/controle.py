"""Controle de execução: toda carga registra o que fez (tabela `controle_execucao`). Carga sem registro não existe."""
from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from . import config as C


def conectar() -> sqlite3.Connection:
    C.WAREHOUSE.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(C.BANCO)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("""CREATE TABLE IF NOT EXISTS controle_execucao (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        etapa TEXT NOT NULL,
        inicio TEXT NOT NULL,
        fim TEXT,
        duracao_s REAL,
        situacao TEXT NOT NULL,           -- EXECUTANDO | OK | FALHA
        detalhe TEXT
    )""")
    return con


@contextmanager
def registrar(con: sqlite3.Connection, etapa: str):
    """Abre o registro antes da etapa e fecha depois, com OK ou FALHA. A exceção é propagada — nunca engolida."""
    t0 = time.perf_counter()
    cur = con.execute("INSERT INTO controle_execucao (etapa, inicio, situacao) VALUES (?, ?, 'EXECUTANDO')",
                      (etapa, datetime.now(timezone.utc).isoformat()))
    con.commit()
    id_exec = cur.lastrowid
    detalhe: dict = {}
    try:
        yield detalhe
    except Exception as e:  # noqa: BLE001 — registra e propaga
        con.execute("UPDATE controle_execucao SET fim=?, duracao_s=?, situacao='FALHA', detalhe=? WHERE id=?",
                    (datetime.now(timezone.utc).isoformat(), round(time.perf_counter() - t0, 3), f"{type(e).__name__}: {e}", id_exec))
        con.commit()
        raise
    con.execute("UPDATE controle_execucao SET fim=?, duracao_s=?, situacao='OK', detalhe=? WHERE id=?",
                (datetime.now(timezone.utc).isoformat(), round(time.perf_counter() - t0, 3), str(detalhe) if detalhe else None, id_exec))
    con.commit()
