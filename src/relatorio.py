"""Etapa 5 — relatório: gráficos (PNG) e tabelas (Markdown) a partir do SPEC, para o estudo de caso do README.

Só lê. Toda regra já foi aplicada nas camadas anteriores; aqui é apresentação.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from . import config as C  # noqa: E402
from .consultar import consultar  # noqa: E402
from .controle import conectar  # noqa: E402

# paleta categórica em ordem fixa (nunca ciclada) + rampa sequencial de um matiz para faixas ordinais
SERIE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
RAMPA = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "legend.frameon": False, "figure.dpi": 130,
})


def br(v, casas=0) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s


def _salvar(fig, nome: str) -> str:
    C.IMAGENS.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(C.IMAGENS / nome, facecolor=SURFACE)
    plt.close(fig)
    return nome


def grafico_churn(con) -> str:
    df = pd.read_sql_query("SELECT mes, id_filial, filial, churn_pct FROM spec_churn_mensal ORDER BY mes", con)
    meses = sorted(df["mes"].unique())[-24:]
    df = df[df["mes"].isin(meses)]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    x = range(len(meses))
    for i, (idf, nome) in enumerate(C.FILIAIS):
        s = df[df["id_filial"] == idf].set_index("mes").reindex(meses)["churn_pct"]
        ax.plot(x, s.values, color=SERIE[i], lw=1.6, label=nome)
        ax.annotate(nome.replace("Filial ", ""), (len(meses) - 1, s.values[-1]), xytext=(4, 0),
                    textcoords="offset points", color=INK2, fontsize=8, va="center")
    t = df[df["id_filial"] == 0].set_index("mes").reindex(meses)["churn_pct"]
    ax.plot(x, t.values, color=INK, lw=2.4, label="Total")
    ax.set_xticks(list(x)[::3], [m[5:] + "/" + m[2:4] for m in meses][::3])
    ax.set_ylim(0)
    ax.set_ylabel("churn mensal (%)")
    ax.set_title("Churn mensal por filial: perdas de cliente ÷ ativos no início do mês (24 meses)")
    ax.legend(ncol=6, loc="upper left", fontsize=8)
    return _salvar(fig, "churn_mensal.png")


def grafico_inadimplencia(con) -> str:
    df = consultar("inadimplencia_faixas", con)
    df = df[df["faixa_dias"] != "TOTAL"]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    barras = ax.bar(df["faixa_dias"], df["valor_vencido"], color=RAMPA, width=0.62, edgecolor=SURFACE, linewidth=2)
    for b, v, p in zip(barras, df["valor_vencido"], df["pct_do_vencido"]):
        ax.annotate(f"R$ {br(v / 1000, 1)} mil\n{br(p, 1)}%", (b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=8.5, color=INK2)
    ax.set_ylim(0, df["valor_vencido"].max() * 1.25)
    ax.yaxis.set_major_formatter(lambda v, _: f"R$ {br(v / 1000)} mil")
    ax.set_xlabel("dias de atraso na data de referência")
    ax.set_title(f"Vencido em aberto por faixa de atraso em {C.DATA_REFERENCIA:%d/%m/%Y}")
    return _salvar(fig, "inadimplencia_faixas.png")


def grafico_ltv(con) -> str:
    df = consultar("ltv", con).sort_values("ltv_esperado_60m")
    fig, ax = plt.subplots(figsize=(9, 4.4))
    y = range(len(df))
    h = 0.36
    ax.barh([i + h / 2 for i in y], df["ltv_esperado_60m"], height=h, color=SERIE[0], label="LTV esperado (ticket × vida esperada, horizonte 60 meses)")
    ax.barh([i - h / 2 for i in y], df["ltv_realizado"], height=h, color=SERIE[1], label="LTV realizado (receita média de quem já saiu)")
    for i, (e, r) in enumerate(zip(df["ltv_esperado_60m"], df["ltv_realizado"])):
        ax.annotate(f"R$ {br(e)}", (e, i + h / 2), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8, color=INK2)
        ax.annotate(f"R$ {br(r)}", (r, i - h / 2), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8, color=INK2)
    ax.set_yticks(list(y), df["plano"])
    ax.set_xlim(0, df["ltv_esperado_60m"].max() * 1.18)
    ax.xaxis.set_major_formatter(lambda v, _: f"R$ {br(v / 1000, 0)} mil")
    ax.grid(axis="y", visible=False)
    ax.set_title("LTV por plano: esperado (horizonte de 60 meses) × realizado")
    ax.legend(loc="lower right", fontsize=8)
    return _salvar(fig, "ltv_plano.png")


def grafico_ativacoes(con) -> str:
    df = pd.read_sql_query("SELECT mes, id_filial, filial, ativacoes FROM spec_ativacoes_filial_mes ORDER BY mes", con)
    meses = sorted(df["mes"].unique())[-18:]
    piv = df[df["mes"].isin(meses)].pivot(index="mes", columns="id_filial", values="ativacoes").reindex(meses).fillna(0)
    fig, ax = plt.subplots(figsize=(10, 4.6))
    base = [0] * len(meses)
    for i, (idf, nome) in enumerate(C.FILIAIS):
        ax.bar(range(len(meses)), piv[idf], bottom=base, color=SERIE[i], label=nome, width=0.7, edgecolor=SURFACE, linewidth=1.5)
        base = [b + v for b, v in zip(base, piv[idf])]
    for i, tot in enumerate(base):
        ax.annotate(br(tot), (i, tot), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8, color=INK2)
    ax.set_xticks(range(len(meses)), [m[5:] + "/" + m[2:4] for m in meses])
    ax.set_ylim(0, max(base) * 1.15)
    ax.set_ylabel("vendas novas")
    ax.set_title("Ativações (vendas novas) por filial e mês: 18 meses")
    ax.legend(ncol=5, loc="upper left", fontsize=8)
    return _salvar(fig, "ativacoes_filial.png")


def grafico_safra(con) -> str:
    df = consultar("safra", con)
    fig, ax = plt.subplots(figsize=(10, 4.4))
    x = range(len(df))
    for i, (col, rot) in enumerate([("retencao_3m_pct", "após 3 meses"), ("retencao_6m_pct", "após 6 meses"), ("retencao_12m_pct", "após 12 meses")]):
        ax.plot(x, df[col], color=SERIE[i], lw=1.8, marker="o", ms=3.5, label=rot)
    ax.set_xticks(list(x)[::3], [m[5:] + "/" + m[2:4] for m in df["safra"]][::3])
    ax.set_ylim(60, 101)
    ax.set_ylabel("% da safra que continua na base")
    ax.set_title("Safra de vendas: retenção após 3, 6 e 12 meses (só conta quem já tem a idade)")
    ax.legend(loc="lower left", fontsize=8)
    return _salvar(fig, "safra_retencao.png")


def markdown(df: pd.DataFrame) -> str:
    def cel(v):
        if isinstance(v, float):
            if pd.isna(v):
                return "—"
            return br(v, 0) if v == int(v) else br(v, 2).rstrip("0").rstrip(",")
        return "—" if v is None else str(v)
    cab = "| " + " | ".join(df.columns) + " |\n|" + "|".join(["---"] * len(df.columns)) + "|\n"
    return cab + "\n".join("| " + " | ".join(cel(v) for v in linha) + " |" for linha in df.itertuples(index=False))


def resultados_md(con, imagens: dict[str, str]) -> None:
    contagens = {t: con.execute(f"SELECT count(*) FROM sor_{t}").fetchone()[0]
                 for t in ("cliente", "contrato", "fatura", "ordem_servico")}
    exec_ = pd.read_sql_query("SELECT etapa, situacao, duracao_s FROM controle_execucao WHERE id > (SELECT COALESCE(MAX(id), 0) - 6 FROM controle_execucao) ORDER BY id", con)
    blocos = [
        ("Churn mensal por filial (últimos 12 meses)", "churn", imagens["churn"]),
        ("Inadimplência por faixa de atraso", "inadimplencia_faixas", imagens["inadimplencia"]),
        ("Inadimplência por filial", "inadimplencia_filial", None),
        ("LTV por plano", "ltv", imagens["ltv"]),
        ("Ativações por filial (últimos 12 meses)", "ativacoes_filial", imagens["ativacoes"]),
        ("Safra de vendas: retenção", "safra", imagens["safra"]),
        ("Ordens de serviço: tempo de fechamento (últimos 12 meses)", "os_tempo_fechamento", None),
    ]
    partes = [
        "# Resultados\n",
        f"> Gerado por `python -m src.pipeline` em {datetime.now(timezone.utc):%d/%m/%Y %H:%M} UTC · base fictícia "
        f"(semente {C.SEMENTE}) · data de referência **{C.DATA_REFERENCIA:%d/%m/%Y}** · "
        + " · ".join(f"{br(q)} {rot}" for rot, q in zip(("clientes", "contratos", "faturas", "ordens de serviço"), contagens.values())) + "\n",
        "\nCada bloco é a saída de um arquivo de `sql/metricas/`. Os números abaixo são os mesmos que as portas de "
        "qualidade conferiram no fim da carga.\n",
    ]
    for titulo, nome, img in blocos:
        partes.append(f"\n## {titulo}\n\n`sql/metricas/{nome}.sql`\n")
        if img:
            partes.append(f"\n![{titulo}](imagens/{img})\n")
        partes.append("\n" + markdown(consultar(nome, con)) + "\n")
    partes.append("\n## Execução registrada\n\n" + markdown(exec_) + "\n")
    C.RESULTADOS.write_text("".join(partes), encoding="utf-8")


def gerar(con: sqlite3.Connection | None = None) -> dict[str, str]:
    con = con or conectar()
    imagens = {
        "churn": grafico_churn(con), "inadimplencia": grafico_inadimplencia(con), "ltv": grafico_ltv(con),
        "ativacoes": grafico_ativacoes(con), "safra": grafico_safra(con),
    }
    resultados_md(con, imagens)
    return imagens


if __name__ == "__main__":
    print(gerar())
