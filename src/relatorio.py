"""Etapa 5 — relatório: gráficos (PNG) e tabelas (Markdown) a partir do SPEC, para o estudo de caso do README.

Só lê. Toda regra já foi aplicada nas camadas anteriores; aqui é apresentação.

Cada gráfico sai em duas versões, `<nome>-claro.png` e `<nome>-escuro.png`, na identidade visual do portfólio
("Placar": grafite, dourado e roxo). O README e o RESULTADOS.md usam `<picture>` com `prefers-color-scheme`
para o GitHub mostrar a versão certa. Fontes (Reddit Sans e JetBrains Mono, licença OFL) em `docs/fontes/`.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

from . import config as C  # noqa: E402
from .consultar import consultar  # noqa: E402
from .controle import conectar  # noqa: E402

# ---------- identidade visual ----------
# Séries das filiais: paleta categórica validada para daltonismo (separação CVD ΔE ≥ 8 entre vizinhas) e com
# contraste ≥ 3:1 sobre o fundo de cada versão. Sem tons de amarelo/ocre nas filiais, para nenhuma se confundir
# com a linha "Total", que é dourada (na versão clara, um dourado mais escuro para passar 3:1).
TEMAS = {
    "claro": {
        "fundo": "#FDFAF3", "ink": "#1C1A17", "ink2": "#5C564D", "muted": "#7A746A", "grid": "#E4DCCB",
        "serie": ["#2a78d6", "#d9541e", "#0f8a68", "#6250d6", "#c2457a"],
        "total": "#8A6508", "roxo": "#7A4DB8", "cinza": "#5C564D",
        "rampa": ["#B89BE0", "#9A74D0", "#7A4DB8", "#5B2A8C", "#3D1A66"],
    },
    "escuro": {
        "fundo": "#1C1922", "ink": "#F2ECE0", "ink2": "#B3ABA0", "muted": "#8E877C", "grid": "#332E3C",
        "serie": ["#3987e5", "#d95926", "#199e70", "#9085e9", "#d55181"],
        "total": "#E8B23A", "roxo": "#B592E6", "cinza": "#B3ABA0",
        "rampa": ["#6B3FA8", "#8A63C8", "#A98AE0", "#C9B3EC", "#E0D3F3"],
    },
}
VERSOES = ("claro", "escuro")
SANS, MONO = "Reddit Sans", "JetBrains Mono"


def _registrar_fontes() -> None:
    pasta = C.RAIZ / "docs" / "fontes"
    for f in sorted(pasta.glob("*.ttf")):
        font_manager.fontManager.addfont(str(f))


def _estilo(t: dict) -> None:
    plt.rcParams.update({
        "figure.facecolor": t["fundo"], "axes.facecolor": t["fundo"], "savefig.facecolor": t["fundo"],
        "axes.edgecolor": t["grid"], "axes.labelcolor": t["ink2"], "xtick.color": t["muted"], "ytick.color": t["muted"],
        "text.color": t["ink"], "axes.grid": True, "grid.color": t["grid"], "grid.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
        "font.family": SANS, "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.titlecolor": t["ink"], "legend.frameon": False, "axes.axisbelow": True,
        "legend.labelcolor": t["ink2"], "figure.dpi": 130,
    })


def _mono(ax) -> None:
    """Números e datas em monoespaçada, como no site."""
    for rot in ax.get_xticklabels() + ax.get_yticklabels():
        rot.set_fontfamily(MONO)


def br(v, casas=0) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _mes_pt(m: str) -> str:
    """'2024-10' -> 'out/2024'."""
    nomes = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    return f"{nomes[int(m[5:7]) - 1]}/{m[:4]}"


def _salvar(fig, nome: str, versao: str) -> str:
    C.IMAGENS.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    arquivo = f"{nome}-{versao}.png"
    fig.savefig(C.IMAGENS / arquivo)
    plt.close(fig)
    return arquivo


def _espalhar(ys: list[float], gap: float) -> list[float]:
    """Afasta rótulos que ficariam sobrepostos no fim das linhas (ordem preservada, deslocamento mínimo)."""
    ordem = sorted(range(len(ys)), key=lambda i: ys[i])
    pos = [ys[i] for i in ordem]
    for k in range(1, len(pos)):
        if pos[k] - pos[k - 1] < gap:
            pos[k] = pos[k - 1] + gap
    # recentra o bloco para não fugir do dado
    desvio = (sum(pos) - sum(ys[i] for i in ordem)) / len(pos)
    pos = [p - desvio for p in pos]
    out = [0.0] * len(ys)
    for k, i in enumerate(ordem):
        out[i] = pos[k]
    return out


# ---------- gráficos ----------
def grafico_churn(con, versao: str) -> str:
    t = TEMAS[versao]
    df = pd.read_sql_query("SELECT mes, id_filial, filial, churn_pct FROM spec_churn_mensal ORDER BY mes", con)
    meses = sorted(df["mes"].unique())[-24:]
    df = df[df["mes"].isin(meses)]
    fig, ax = plt.subplots(figsize=(10, 4.6))
    x = range(len(meses))
    finais = []
    for i, (idf, nome) in enumerate(C.FILIAIS):
        s = df[df["id_filial"] == idf].set_index("mes").reindex(meses)["churn_pct"]
        ax.plot(x, s.values, color=t["serie"][i], lw=1.6)
        finais.append((nome.replace("Filial ", ""), float(s.values[-1]), t["serie"][i], False))
    total = df[df["id_filial"] == 0].set_index("mes").reindex(meses)["churn_pct"]
    ax.plot(x, total.values, color=t["total"], lw=2.6)
    finais.append(("Total", float(total.values[-1]), t["total"], True))
    topo = max(df["churn_pct"].max(), total.max()) * 1.12
    ax.set_ylim(0, topo)
    ys = _espalhar([f[1] for f in finais], topo * 0.055)
    for (rot, _, cor, forte), y in zip(finais, ys):
        ax.annotate(rot, (len(meses) - 1, y), xytext=(6, 0), textcoords="offset points", color=cor if forte else t["ink2"],
                    fontsize=8.5, va="center", fontweight="bold" if forte else "normal")
    ax.set_xticks(list(x)[::3], [m[5:] + "/" + m[2:4] for m in meses][::3])
    ax.set_ylabel("churn mensal (%)")
    ax.set_title(f"Churn mensal por filial: perdas de cliente ÷ ativos no início do mês · {_mes_pt(meses[0])} a {_mes_pt(meses[-1])} ({len(meses)} meses)")
    _mono(ax)
    return _salvar(fig, "churn_mensal", versao)


def grafico_inadimplencia(con, versao: str) -> str:
    t = TEMAS[versao]
    df = consultar("inadimplencia_faixas", con)
    df = df[df["faixa_dias"] != "TOTAL"]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    barras = ax.bar(df["faixa_dias"], df["valor_vencido"], color=t["rampa"], width=0.62, edgecolor=t["fundo"], linewidth=2)
    for b, v, p in zip(barras, df["valor_vencido"], df["pct_do_vencido"]):
        ax.annotate(f"R$ {br(v / 1000, 1)} mil\n{br(p, 1)}%", (b.get_x() + b.get_width() / 2, b.get_height()),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=8.5, color=t["ink2"], fontfamily=MONO)
    ax.set_ylim(0, df["valor_vencido"].max() * 1.25)
    ax.yaxis.set_major_formatter(lambda v, _: f"R$ {br(v / 1000)} mil")
    ax.set_xlabel("dias de atraso na data de referência")
    ax.set_title(f"Vencido em aberto por faixa de atraso em {C.DATA_REFERENCIA:%d/%m/%Y}")
    _mono(ax)
    return _salvar(fig, "inadimplencia_faixas", versao)


def grafico_ltv(con, versao: str) -> str:
    t = TEMAS[versao]
    df = consultar("ltv", con).sort_values("ltv_esperado_60m")
    fig, ax = plt.subplots(figsize=(9, 4.4))
    y = range(len(df))
    h = 0.36
    ax.barh([i + h / 2 for i in y], df["ltv_esperado_60m"], height=h, color=t["total"], label="LTV esperado (ticket × vida esperada, horizonte 60 meses)")
    ax.barh([i - h / 2 for i in y], df["ltv_realizado"], height=h, color=t["roxo"], label="LTV realizado (receita média de quem já saiu)")
    for i, (e, r) in enumerate(zip(df["ltv_esperado_60m"], df["ltv_realizado"])):
        ax.annotate(f"R$ {br(e)}", (e, i + h / 2), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8, color=t["ink2"], fontfamily=MONO)
        ax.annotate(f"R$ {br(r)}", (r, i - h / 2), xytext=(4, 0), textcoords="offset points", va="center", fontsize=8, color=t["ink2"], fontfamily=MONO)
    ax.set_yticks(list(y), df["plano"])
    ax.set_xlim(0, df["ltv_esperado_60m"].max() * 1.18)
    ax.xaxis.set_major_formatter(lambda v, _: f"R$ {br(v / 1000, 0)} mil")
    ax.grid(axis="y", visible=False)
    ax.set_title("LTV por plano: esperado (horizonte de 60 meses) × realizado")
    ax.legend(loc="lower right", fontsize=8)
    _mono(ax)
    for rot in ax.get_yticklabels():      # nomes de plano em Reddit Sans, não em mono
        rot.set_fontfamily(SANS)
    return _salvar(fig, "ltv_plano", versao)


def grafico_ativacoes(con, versao: str) -> str:
    t = TEMAS[versao]
    df = pd.read_sql_query("SELECT mes, id_filial, filial, ativacoes FROM spec_ativacoes_filial_mes ORDER BY mes", con)
    meses = sorted(df["mes"].unique())[-18:]
    piv = df[df["mes"].isin(meses)].pivot(index="mes", columns="id_filial", values="ativacoes").reindex(meses).fillna(0)
    fig, ax = plt.subplots(figsize=(10, 4.6))
    base = [0] * len(meses)
    for i, (idf, nome) in enumerate(C.FILIAIS):
        ax.bar(range(len(meses)), piv[idf], bottom=base, color=t["serie"][i], label=nome, width=0.7, edgecolor=t["fundo"], linewidth=1.5)
        base = [b + v for b, v in zip(base, piv[idf])]
    for i, tot in enumerate(base):
        ax.annotate(br(tot), (i, tot), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=8, color=t["ink2"], fontfamily=MONO)
    ax.set_xticks(range(len(meses)), [m[5:] + "/" + m[2:4] for m in meses])
    ax.set_ylim(0, max(base) * 1.15)
    ax.set_ylabel("vendas novas")
    ax.set_title(f"Ativações (vendas novas) por filial e mês · {_mes_pt(meses[0])} a {_mes_pt(meses[-1])} ({len(meses)} meses)")
    ax.legend(ncol=5, loc="upper left", fontsize=8)
    _mono(ax)
    return _salvar(fig, "ativacoes_filial", versao)


def grafico_safra(con, versao: str) -> str:
    t = TEMAS[versao]
    df = consultar("safra", con)
    fig, ax = plt.subplots(figsize=(10, 4.4))
    x = range(len(df))
    series = [("retencao_3m_pct", "após 3 meses", t["cinza"], 1.6), ("retencao_6m_pct", "após 6 meses", t["roxo"], 1.8), ("retencao_12m_pct", "após 12 meses", t["total"], 2.2)]
    for col, rot, cor, lw in series:
        ax.plot(x, df[col], color=cor, lw=lw, marker="o", ms=3.5, label=rot)
    ax.set_xticks(list(x)[::3], [m[5:] + "/" + m[2:4] for m in df["safra"]][::3])
    ax.set_ylim(60, 101)
    ax.set_ylabel("% da safra que continua na base")
    ax.set_title(f"Safra de vendas: retenção após 3, 6 e 12 meses · safras de {_mes_pt(df['safra'].iloc[0])} a {_mes_pt(df['safra'].iloc[-1])} (só conta quem já tem a idade)")
    ax.legend(loc="lower left", fontsize=8)
    _mono(ax)
    return _salvar(fig, "safra_retencao", versao)


GRAFICOS = {
    "churn": grafico_churn, "inadimplencia": grafico_inadimplencia, "ltv": grafico_ltv,
    "ativacoes": grafico_ativacoes, "safra": grafico_safra,
}


# ---------- tabelas e RESULTADOS.md ----------
def markdown(df: pd.DataFrame) -> str:
    def cel(v):
        if isinstance(v, float):
            if pd.isna(v):
                return "—"
            return br(v, 0) if v == int(v) else br(v, 2).rstrip("0").rstrip(",")
        return "—" if v is None else str(v)
    cab = "| " + " | ".join(df.columns) + " |\n|" + "|".join(["---"] * len(df.columns)) + "|\n"
    return cab + "\n".join("| " + " | ".join(cel(v) for v in linha) + " |" for linha in df.itertuples(index=False))


def picture(nome: str, alt: str, pasta: str = "imagens") -> str:
    """Tag <picture>: o GitHub escolhe a versão escura ou clara conforme o tema de quem lê."""
    return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="{pasta}/{nome}-escuro.png">\n'
            f'  <img alt="{alt}" src="{pasta}/{nome}-claro.png">\n</picture>')


def _leituras(con) -> dict[str, str]:
    """Uma ou duas frases por métrica, calculadas dos mesmos dados das tabelas (nunca escritas à mão)."""
    def um(sql, *a):
        return con.execute(sql, a).fetchone()[0]
    meses = [r[0] for r in con.execute("SELECT DISTINCT mes FROM spec_churn_mensal ORDER BY mes")]
    ult12 = meses[-12:]
    marcas = ",".join("?" * 12)
    L = {}
    # churn
    perdas, expo = con.execute(f"SELECT SUM(perdas), SUM(ativos_inicio) FROM spec_churn_mensal WHERE id_filial = 0 AND mes IN ({marcas})", ult12).fetchone()
    churn12 = 100 * perdas / expo
    pior = con.execute(f"SELECT filial, 100.0 * SUM(perdas) / SUM(ativos_inicio) FROM spec_churn_mensal WHERE id_filial <> 0 AND mes IN ({marcas}) GROUP BY filial ORDER BY 2 DESC LIMIT 1", ult12).fetchone()
    melhor = con.execute(f"SELECT filial, 100.0 * SUM(perdas) / SUM(ativos_inicio) FROM spec_churn_mensal WHERE id_filial <> 0 AND mes IN ({marcas}) GROUP BY filial ORDER BY 2 ASC LIMIT 1", ult12).fetchone()
    ini_base = um("SELECT ativos_inicio FROM spec_churn_mensal WHERE id_filial = 0 AND mes = ?", ult12[0])
    fim_base = um("SELECT SUM(ativos_fim) FROM sot_base_mensal WHERE mes = ?", ult12[-1])
    L["churn"] = (f"Churn consolidado de **{br(churn12, 2)}% ao mês** nos últimos 12 meses ({_mes_pt(ult12[0])} a {_mes_pt(ult12[-1])}), "
                  f"cerca de {br(100 * (1 - (1 - churn12 / 100) ** 12), 0)}% ao ano, com a base ativa indo de {br(ini_base)} para {br(fim_base)} contratos. "
                  f"{pior[0]} tem o maior churn médio do período ({br(pior[1], 2)}%) e {melhor[0]} o menor ({br(melhor[1], 2)}%).")
    # inadimplência por faixa
    total = um("SELECT SUM(valor) FROM sot_titulo WHERE situacao = 'VENCIDO'")
    contratos = um("SELECT count(DISTINCT id_contrato) FROM sot_titulo WHERE situacao = 'VENCIDO'")
    pct181 = 100 * um("SELECT SUM(valor) FROM sot_titulo WHERE situacao = 'VENCIDO' AND faixa_atraso = '181+'") / total
    pct_canc = 100 * um("SELECT SUM(t.valor) FROM sot_titulo t JOIN sot_contrato c USING (id_contrato) WHERE t.situacao = 'VENCIDO' AND c.situacao <> 'ATIVO'") / total
    soma_faixas = um("SELECT SUM(contratos) FROM spec_inadimplencia_faixa")
    L["inadimplencia_faixas"] = (f"**R$ {br(total)}** vencidos em aberto em {C.DATA_REFERENCIA:%d/%m/%Y}, em {br(contratos)} contratos distintos. "
                                 f"{br(pct181, 1)}% do valor tem mais de 180 dias, e {br(pct_canc, 1)}% do vencido está em contratos já cancelados: "
                                 f"é dívida de quem saiu, não de quem está na base.")
    L["nota:inadimplencia_faixas"] = (f"> **Nota:** a linha TOTAL soma a coluna `contratos` das faixas ({br(soma_faixas)}); um contrato com títulos em mais de uma faixa "
                                      f"conta em cada uma. Contratos distintos com vencido: {br(contratos)}. Corrigir o TOTAL no SQL para contar distintos, "
                                      f"com teste, é o próximo passo (fora desta versão, que é só de apresentação).")
    # inadimplência por filial
    fil = con.execute("""WITH a AS (SELECT id_filial, count(*) n FROM sot_contrato WHERE situacao = 'ATIVO' GROUP BY id_filial),
        v AS (SELECT t.id_filial, count(DISTINCT t.id_contrato) n FROM sot_titulo t JOIN sot_contrato c USING (id_contrato)
              WHERE t.situacao = 'VENCIDO' AND c.situacao = 'ATIVO' GROUP BY t.id_filial)
        SELECT f.nome, 100.0 * v.n / a.n, SUM(v.n) OVER (), SUM(a.n) OVER () FROM sor_filial f JOIN a USING (id_filial) JOIN v USING (id_filial) ORDER BY 2 DESC""").fetchall()
    L["inadimplencia_filial"] = (f"Entre os contratos **ativos**, {br(fil[0][2])} de {br(fil[0][3])} ({br(100 * fil[0][2] / fil[0][3], 1)}%) têm algum título vencido. "
                                 f"{fil[0][0]} tem a maior taxa ({br(fil[0][1], 1)}%) e {fil[-1][0]} a menor ({br(fil[-1][1], 1)}%).")
    # LTV
    top = con.execute("SELECT plano, ltv_esperado_60m, ltv_realizado FROM spec_ltv_plano ORDER BY ltv_esperado_60m DESC LIMIT 1").fetchone()
    base = con.execute("SELECT plano, ltv_esperado_60m, ltv_realizado FROM spec_ltv_plano ORDER BY ltv_esperado_60m ASC LIMIT 1").fetchone()
    r_min, r_max = con.execute("SELECT MIN(100.0 * ltv_realizado / ltv_esperado_60m), MAX(100.0 * ltv_realizado / ltv_esperado_60m) FROM spec_ltv_plano").fetchone()
    meses_casa = um("SELECT ROUND(SUM(meses_de_casa_encerrados * contratos_encerrados) / SUM(contratos_encerrados), 1) FROM spec_ltv_plano")   # ponderada pelos contratos
    L["ltv"] = (f"O LTV esperado com horizonte de 60 meses vai de **R$ {br(base[1])}** ({base[0]}) a **R$ {br(top[1])}** ({top[0]}). "
                f"Em cada plano o realizado fica entre {br(r_min, 0)}% e {br(r_max, 0)}% do esperado: o padrão se repete, porque o realizado só enxerga quem já saiu, com {br(meses_casa, 1)} meses de casa em média.")
    # ativações
    def vendas(n):
        ms = meses[-n:]
        tot = um(f"SELECT SUM(ativacoes) FROM spec_ativacoes_filial_mes WHERE mes IN ({','.join('?' * n)})", *ms)
        cen = um(f"SELECT SUM(ativacoes) FROM spec_ativacoes_filial_mes WHERE id_filial = 1 AND mes IN ({','.join('?' * n)})", *ms)
        return tot, 100 * cen / tot, ms
    t12, c12, _ = vendas(12); t18, c18, _ = vendas(18); tall, call, _ = vendas(len(meses))
    lider = con.execute(f"SELECT filial, SUM(ativacoes) FROM spec_ativacoes_filial_mes WHERE mes IN ({marcas}) GROUP BY filial ORDER BY 2 DESC LIMIT 1", ult12).fetchone()
    L["ativacoes_filial"] = (f"**{br(t12)} vendas novas** nos últimos 12 meses da tabela ({br(t18)} nos 18 meses do gráfico; {br(tall)} na série inteira). "
                             f"{lider[0]} lidera com {br(lider[1])} no ano, {br(c12, 0)}% do total.")
    # safra
    r3, r6, r12 = con.execute("SELECT AVG(retencao_3m_pct), AVG(retencao_6m_pct), AVG(retencao_12m_pct) FROM spec_safra_retencao").fetchone()
    n12 = um("SELECT count(*) FROM spec_safra_retencao WHERE retencao_12m_pct IS NOT NULL")
    L["safra"] = (f"Em média, **{br(r3, 0)}%** de cada safra de vendas continua na base após 3 meses, {br(r6, 0)}% após 6 e {br(r12, 0)}% após 12 "
                  f"(a retenção de 12 meses só conta as {n12} safras que já têm essa idade).")
    # O.S.
    os_ = consultar("os_tempo_fechamento", con)
    rep = os_[os_["assunto"] == "REPARO"].iloc[0] if (os_["assunto"] == "REPARO").any() else os_.iloc[0]
    abertas = int(os_["abertas"].sum())
    L["os_tempo_fechamento"] = (f"Nos últimos 12 meses, {br(int(os_['fechadas'].sum()))} ordens de serviço foram fechadas e {br(abertas)} seguem abertas. "
                                f"Reparo leva {br(rep['mediana_dias'], 1)} dia{'' if rep['mediana_dias'] == 1 else 's'} na mediana ({br(rep['media_dias'], 1)} na média): a mediana é a que vale, porque poucas O.S. longas puxam a média.")
    return L


def _tabela(df: pd.DataFrame, limite: int = 12) -> str:
    """Tabela curta fica aberta; tabela longa fica recolhida num <details>."""
    md = markdown(df)
    if len(df) <= limite:
        return md
    return f"<details>\n<summary>Tabela completa ({len(df)} linhas)</summary>\n\n{md}\n\n</details>"


def resultados_md(con, imagens: dict[str, str]) -> None:
    contagens = {t: con.execute(f"SELECT count(*) FROM sor_{t}").fetchone()[0]
                 for t in ("cliente", "contrato", "fatura", "ordem_servico")}
    exec_ = pd.read_sql_query("""
        SELECT etapa, situacao, duracao_s FROM controle_execucao
        WHERE id >= (SELECT MAX(id) FROM controle_execucao WHERE etapa = 'carregar_sor'
                     AND id < (SELECT MAX(id) FROM controle_execucao WHERE etapa = 'portas'))
          AND id <= (SELECT MAX(id) FROM controle_execucao WHERE etapa = 'portas')
        ORDER BY id""", con)
    leituras = _leituras(con)
    n_churn = len(sorted(pd.read_sql_query("SELECT DISTINCT mes FROM spec_churn_mensal", con)["mes"])[-24:])
    n_ativ = len(sorted(pd.read_sql_query("SELECT DISTINCT mes FROM spec_ativacoes_filial_mes", con)["mes"])[-18:])
    # (título, consulta, imagem, alt, nota de período)
    blocos = [
        ("Churn mensal por filial", "churn", imagens["churn"], "Churn mensal por filial", f"gráfico: últimos {n_churn} meses · tabela: últimos 12 meses"),
        ("Inadimplência por faixa de atraso", "inadimplencia_faixas", imagens["inadimplencia"], "Vencido em aberto por faixa de atraso", f"posição em {C.DATA_REFERENCIA:%d/%m/%Y}"),
        ("Inadimplência por filial", "inadimplencia_filial", None, "", f"contratos ativos em {C.DATA_REFERENCIA:%d/%m/%Y}"),
        ("LTV por plano", "ltv", imagens["ltv"], "LTV por plano: esperado × realizado", "ticket e churn dos últimos 12 meses; realizado de todos os contratos encerrados"),
        ("Ativações por filial", "ativacoes_filial", imagens["ativacoes"], "Ativações por filial e mês", f"gráfico: últimos {n_ativ} meses · tabela: últimos 12 meses"),
        ("Safra de vendas: retenção", "safra", imagens["safra"], "Retenção por safra após 3, 6 e 12 meses", "todas as safras da série; cada coluna só conta quem já tem a idade"),
        ("Ordens de serviço: tempo de fechamento", "os_tempo_fechamento", None, "", "abertas nos últimos 12 meses"),
    ]
    partes = [
        "# Resultados\n",
        f"> Gerado por `python -m src.pipeline` em {datetime.now(timezone.utc):%d/%m/%Y %H:%M} UTC · base fictícia "
        f"(semente {C.SEMENTE}) · data de referência **{C.DATA_REFERENCIA:%d/%m/%Y}** · "
        + " · ".join(f"{br(q)} {rot}" for rot, q in zip(("clientes", "contratos", "faturas", "ordens de serviço"), contagens.values())) + "\n",
        "\nCada bloco é a saída de um arquivo de `sql/metricas/`. Os números abaixo são os mesmos que as portas de "
        "qualidade conferiram no fim da carga; as frases de leitura também são calculadas dos dados, a cada execução.\n",
        "\n**Índice:** " + " · ".join(f"[{t}](#{t.lower().replace(' ', '-').replace(':', '').replace(',', '')})" for t, *_ in blocos) + "\n",
    ]
    for titulo, nome, img, alt, periodo in blocos:
        partes.append(f"\n## {titulo}\n\n`sql/metricas/{nome}.sql` · {periodo}\n")
        if img:
            partes.append("\n" + picture(img, alt) + "\n")
        partes.append("\n" + leituras[nome] + "\n")
        partes.append("\n" + _tabela(consultar(nome, con)) + "\n")
        if "nota:" + nome in leituras:
            partes.append("\n" + leituras["nota:" + nome] + "\n")
    partes.append("\n## Execução registrada\n\nEtapas da última execução do pipeline (`controle_execucao`).\n\n" + markdown(exec_) + "\n")
    C.RESULTADOS.write_text("".join(partes), encoding="utf-8")


def gerar(con: sqlite3.Connection | None = None) -> dict[str, str]:
    """Gera cada gráfico nas duas versões e devolve o nome-base de cada um (sem sufixo e sem extensão)."""
    con = con or conectar()
    _registrar_fontes()
    imagens = {}
    for chave, fn in GRAFICOS.items():
        for versao in VERSOES:
            _estilo(TEMAS[versao])
            arquivo = fn(con, versao)
        imagens[chave] = arquivo.replace(f"-{VERSOES[-1]}.png", "")
    resultados_md(con, imagens)
    return imagens


if __name__ == "__main__":
    print(gerar())
