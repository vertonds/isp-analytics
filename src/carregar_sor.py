"""Etapa 1 — Stage → SOR (System of Record).

O SOR é a cópia TIPADA e íntegra da extração: datas em ISO, valores em número, chaves declaradas. Nenhuma regra de
negócio entra aqui. Três proteções, copiadas do que deu certo no projeto real:
  1. partição sem marcador `_completa.json` não entra;
  2. a contagem do CSV tem de bater com a do marcador;
  3. porta de volume: queda > 50% sobre uma tabela que já tinha >= 200 linhas bloqueia a carga.
A carga é substituição integral dentro de uma transação — rodar duas vezes dá o mesmo resultado (idempotente).
"""
from __future__ import annotations

import json
import sqlite3

import pandas as pd

from . import config as C
from .controle import conectar, registrar

TABELAS = ["filial", "plano", "cliente", "contrato", "fatura", "ordem_servico"]
COLUNAS_DATA = {
    "cliente": ["data_cadastro"],
    "contrato": ["data_ativacao", "data_cancelamento"],
    "fatura": ["competencia", "data_vencimento", "data_pagamento", "data_emissao"],
    "ordem_servico": ["data_abertura", "data_fechamento"],
}
COLUNAS_VALOR = {"plano": ["valor"], "contrato": ["valor_contrato"], "fatura": ["valor"]}


class CargaBloqueada(RuntimeError):
    """A resposta a um bloqueio é recoletar — nunca contornar a porta."""


def ler_stage(tabela: str) -> pd.DataFrame:
    pasta = C.STAGE / tabela
    marcador = pasta / "_completa.json"
    if not marcador.exists():
        raise CargaBloqueada(f"{tabela}: partição sem marcador de conclusão (_completa.json)")
    esperado = json.loads(marcador.read_text(encoding="utf-8"))["linhas"]
    df = pd.read_csv(pasta / f"{tabela}.csv", sep=";", dtype=str, keep_default_na=False, encoding="utf-8")
    if len(df) != esperado:
        raise CargaBloqueada(f"{tabela}: CSV com {len(df)} linhas, marcador diz {esperado}")
    for c in COLUNAS_DATA.get(tabela, []):
        df[c] = pd.to_datetime(df[c].replace("", None), format="%d/%m/%Y").dt.strftime("%Y-%m-%d")
    for c in COLUNAS_VALOR.get(tabela, []):
        df[c] = pd.to_numeric(df[c].str.replace(",", ".", regex=False))
    df = df.astype(object).where(df.notna(), None)
    for c in df.columns:
        if c.startswith("id_") or c in ("velocidade_mbps",):
            df[c] = df[c].map(lambda v: int(v) if v not in (None, "") else None)
    return df


def porta_de_volume(con: sqlite3.Connection, tabela: str, novo: int) -> None:
    atual = con.execute(f"SELECT count(*) FROM sor_{tabela}").fetchone()[0]
    if atual >= 200 and novo < atual * 0.5:
        raise CargaBloqueada(f"{tabela}: volume caiu de {atual} para {novo} (> 50%) — carga bloqueada, recoletar")


def carregar(con: sqlite3.Connection | None = None) -> dict[str, int]:
    con = con or conectar()
    con.executescript((C.SQL / "01_stage_sor" / "ddl.sql").read_text(encoding="utf-8"))
    contagens = {}
    with registrar(con, "carregar_sor") as detalhe:
        quadros = {}
        for t in TABELAS:                               # 1) lê e valida TODAS as partições antes de tocar no banco
            quadros[t] = ler_stage(t)
            porta_de_volume(con, t, len(quadros[t]))
        with con:                                       # 2) uma transação só: ou troca tudo, ou nada
            for t in reversed(TABELAS):                 #    apaga dos filhos para os pais (chave estrangeira ligada)
                con.execute(f"DELETE FROM sor_{t}")
            for t in TABELAS:                           #    insere dos pais para os filhos
                df = quadros[t]
                cols = ", ".join(df.columns)
                marcas = ", ".join("?" * len(df.columns))
                con.executemany(f"INSERT INTO sor_{t} ({cols}) VALUES ({marcas})", df.itertuples(index=False, name=None))
                contagens[t] = len(df)
        detalhe.update(contagens)
    return contagens


if __name__ == "__main__":
    for t, q in carregar().items():
        print(f"sor_{t:15s} {q:>8,d} linhas")
