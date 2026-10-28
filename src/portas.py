"""Portas de qualidade: invariantes que a carga tem de respeitar. Rodam no fim do pipeline e nos testes — o mesmo código.

Porta permanente BLOQUEIA (levanta exceção); nunca «ajusta» o número para passar.
"""
from __future__ import annotations

import json
import sqlite3

from . import config as C


class PortaFalhou(AssertionError):
    pass


def _um(con: sqlite3.Connection, sql: str):
    return con.execute(sql).fetchone()[0]


def stage_igual_sor(con: sqlite3.Connection) -> dict:
    """Completude: cada tabela do SOR tem exatamente as linhas que o marcador do Stage declarou."""
    out = {}
    for t in ("filial", "plano", "cliente", "contrato", "fatura", "ordem_servico"):
        esperado = json.loads((C.STAGE / t / "_completa.json").read_text(encoding="utf-8"))["linhas"]
        real = _um(con, f"SELECT count(*) FROM sor_{t}")
        if real != esperado:
            raise PortaFalhou(f"sor_{t}: {real} linhas, Stage declarou {esperado}")
        out[t] = real
    return out


def nenhum_titulo_cancelado_no_sot(con: sqlite3.Connection) -> int:
    """Status 'C' nunca alimenta indicador: o SOT de títulos não pode ter nenhum."""
    q = _um(con, "SELECT count(*) FROM sot_titulo WHERE status = 'C'")
    if q:
        raise PortaFalhou(f"sot_titulo tem {q} títulos cancelados")
    return _um(con, "SELECT count(*) FROM sot_titulo")


def fluxo_da_base_fecha(con: sqlite3.Connection) -> int:
    """Invariante do fluxo: ativos no fim = ativos no início + entradas − saídas, e o fim de um mês é o início do seguinte."""
    quebras = _um(con, "SELECT count(*) FROM sot_base_mensal WHERE ativos_fim <> ativos_inicio + entradas - saidas")
    if quebras:
        raise PortaFalhou(f"{quebras} linhas de sot_base_mensal não fecham o fluxo")
    emendas = _um(con, """
        SELECT count(*) FROM sot_base_mensal a
        JOIN sot_base_mensal b ON b.id_filial = a.id_filial AND b.mes = strftime('%Y-%m', date(a.dia_inicio, '+1 month'))
        WHERE b.ativos_inicio <> a.ativos_fim""")
    if emendas:
        raise PortaFalhou(f"{emendas} emendas mês→mês não batem (fim de um ≠ início do outro)")
    return _um(con, "SELECT count(*) FROM sot_base_mensal")


def faixas_somam_o_total(con: sqlite3.Connection) -> float:
    """Decomposição: a soma das faixas de atraso reproduz o total vencido em aberto (R$ 0,01 de tolerância)."""
    faixas = _um(con, "SELECT COALESCE(SUM(valor), 0) FROM spec_inadimplencia_faixa")
    total = _um(con, "SELECT COALESCE(SUM(valor), 0) FROM sot_titulo WHERE situacao = 'VENCIDO'")
    if abs(faixas - total) > 0.01:
        raise PortaFalhou(f"faixas somam {faixas:.2f}, total vencido é {total:.2f}")
    return total


def churn_total_e_soma_das_filiais(con: sqlite3.Connection) -> int:
    """Agregado = detalhe: as perdas da linha TOTAL são a soma das filiais em cada mês."""
    q = _um(con, """
        SELECT count(*) FROM spec_churn_mensal t
        JOIN (SELECT mes, SUM(perdas) p, SUM(ativos_inicio) a FROM spec_churn_mensal WHERE id_filial <> 0 GROUP BY mes) f USING (mes)
        WHERE t.id_filial = 0 AND (t.perdas <> f.p OR t.ativos_inicio <> f.a)""")
    if q:
        raise PortaFalhou(f"{q} meses em que o TOTAL do churn não é a soma das filiais")
    return _um(con, "SELECT count(*) FROM spec_churn_mensal WHERE id_filial = 0")


def ativacoes_batem_com_a_base(con: sqlite3.Connection) -> int:
    """O mesmo número em duas telas: ativações do SPEC = vendas novas do SOT, mês a mês e por filial."""
    q = _um(con, """
        SELECT count(*) FROM spec_ativacoes_filial_mes s JOIN sot_base_mensal b USING (mes, id_filial)
        WHERE s.ativacoes <> b.vendas_novas""")
    if q:
        raise PortaFalhou(f"{q} linhas de ativações divergem da base mensal")
    return _um(con, "SELECT SUM(ativacoes) FROM spec_ativacoes_filial_mes")


TODAS = [stage_igual_sor, nenhum_titulo_cancelado_no_sot, fluxo_da_base_fecha, faixas_somam_o_total,
         churn_total_e_soma_das_filiais, ativacoes_batem_com_a_base]


def conferir(con: sqlite3.Connection) -> dict[str, object]:
    return {p.__name__: p(con) for p in TODAS}
