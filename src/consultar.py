"""Roda uma consulta de `sql/metricas/` e imprime o resultado como tabela.

    python -m src.consultar churn
    python -m src.consultar inadimplencia_faixas --md     # saída em Markdown
"""
from __future__ import annotations

import sys

import pandas as pd

from . import config as C
from .camadas import _preparar
from .controle import conectar


def consultar(nome: str, con=None) -> pd.DataFrame:
    con = con or conectar()
    sql = _preparar((C.SQL / "metricas" / f"{nome}.sql").read_text(encoding="utf-8"))
    return pd.read_sql_query(sql, con)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    df = consultar(sys.argv[1])
    if "--md" in sys.argv:
        from .relatorio import markdown
        print(markdown(df))
    else:
        print(df.to_string(index=False))
