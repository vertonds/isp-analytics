"""Etapa 0 — gera a extração fictícia (Stage) de um provedor de internet.

Tudo aqui é sintético: nomes, endereços e documentos vêm da Faker; o comportamento (quando se vende, quando se
cancela, quem paga atrasado, quantas O.S. abrem) vem de distribuições NumPy com semente fixa. A saída imita o que
um ERP entregaria: CSV com ';', datas dd/mm/aaaa, vírgula decimal, códigos de status de uma letra e um marcador
`_completa.json` por tabela — a carga seguinte só aceita partição com marcador.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone

import numpy as np
import pandas as pd
from faker import Faker

from . import config as C


def meses_entre(ini: date, fim: date) -> list[date]:
    """Primeiro dia de cada mês de `ini` até o mês de `fim`."""
    out, d = [], date(ini.year, ini.month, 1)
    while d <= fim:
        out.append(d)
        d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return out


def dias_no_mes(d: date) -> int:
    prox = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    return (prox - d).days


def _hash_documento(doc: str) -> str:
    """O dado pessoal não persiste: só o resumo (como no projeto real, que usa HMAC com chave fora do repositório)."""
    return hashlib.sha256(doc.encode()).hexdigest()[:32]


def _para_erp_data(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s).dt.strftime("%d/%m/%Y").where(s.notna(), "")


def _para_erp_valor(s: pd.Series) -> pd.Series:
    return s.map(lambda v: "" if pd.isna(v) else f"{v:.2f}".replace(".", ","))


def gerar() -> dict[str, int]:
    rng = np.random.default_rng(C.SEMENTE)
    Faker.seed(C.SEMENTE)
    fake = Faker("pt_BR")
    ref = C.DATA_REFERENCIA
    meses_hist = meses_entre(C.INICIO_HISTORICO, C.INICIO_PERIODO - timedelta(days=1))
    meses_per = meses_entre(C.INICIO_PERIODO, ref)
    meses_todos = meses_hist + meses_per
    idx_mes = {m: i for i, m in enumerate(meses_todos)}

    # ---------- filiais e planos ----------
    filiais = pd.DataFrame(C.FILIAIS, columns=["id_filial", "nome"])
    filiais["cidade"] = [fake.city() for _ in range(len(filiais))]
    planos = pd.DataFrame(C.PLANOS, columns=["id_plano", "nome", "velocidade_mbps", "valor", "segmento"])

    # ---------- contratos: quando foram ativados ----------
    n_h, n_p = C.N_CONTRATOS_HISTORICO, C.N_CONTRATOS_PERIODO
    peso_h = np.linspace(1.0, 1.3, len(meses_hist))
    sazonal = {1: 0.85, 2: 0.90, 3: 1.05, 4: 1.0, 5: 1.0, 6: 0.95, 7: 1.10, 8: 1.10, 9: 1.05, 10: 1.0, 11: 0.95, 12: 0.90}
    peso_p = np.linspace(1.0, 1.7, len(meses_per)) * np.array([sazonal[m.month] for m in meses_per])
    mes_ativ = np.concatenate([
        rng.choice(len(meses_hist), n_h, p=peso_h / peso_h.sum()),
        len(meses_hist) + rng.choice(len(meses_per), n_p, p=peso_p / peso_p.sum()),
    ])
    n = n_h + n_p
    dia_ativ = np.array([rng.integers(1, dias_no_mes(meses_todos[m]) + 1) for m in mes_ativ])
    data_ativ = np.array([meses_todos[m].replace(day=int(d)) for m, d in zip(mes_ativ, dia_ativ)])

    id_filial = rng.choice([f[0] for f in C.FILIAIS], n, p=C.PESO_FILIAL)
    id_plano = rng.choice([p[0] for p in C.PLANOS], n, p=C.PESO_PLANO)
    motivo_inc = rng.choice(C.MOTIVOS_INCLUSAO, n, p=C.PESO_MOTIVO_INCLUSAO)
    desconto = np.where(rng.random(n) < 0.15, 0.10, 0.0)
    valor_plano = planos.set_index("id_plano").loc[id_plano, "valor"].to_numpy()
    valor_contrato = np.round(valor_plano * (1 - desconto), 2)

    # ---------- cancelamento: risco mensal que depende de filial, plano e idade ----------
    f_filial = np.array([C.FATOR_RISCO_FILIAL[f] for f in id_filial])
    f_plano = np.array([C.FATOR_RISCO_PLANO[p] for p in id_plano])
    mes_canc = np.full(n, -1)
    vivo = np.ones(n, dtype=bool)
    for k in range(1, len(meses_todos) + 1):            # k = idade em meses no mês avaliado
        f_idade = next(f for lim, f in C.FATOR_RISCO_IDADE if k <= lim)
        risco = C.RISCO_MENSAL_BASE * f_filial * f_plano * f_idade
        alvo = vivo & (mes_ativ + k < len(meses_todos))  # só meses dentro do histórico
        sorteio = rng.random(n) < risco
        cai = alvo & sorteio
        mes_canc[cai] = mes_ativ[cai] + k
        vivo &= ~cai
    data_canc = np.array([
        None if m < 0 else meses_todos[m].replace(day=int(rng.integers(1, dias_no_mes(meses_todos[m]) + 1)))
        for m in mes_canc
    ], dtype=object)
    motivo_canc = np.where(mes_canc >= 0, rng.choice(C.MOTIVOS_CANCELAMENTO, n, p=C.PESO_MOTIVO_CANCELAMENTO), None)

    # ---------- clientes (alguns com mais de um contrato) ----------
    n_cli = int(n * (1 - C.PROPORCAO_CLIENTES_COM_2_CONTRATOS))
    id_cliente = np.concatenate([np.arange(1, n_cli + 1), rng.integers(1, n_cli + 1, n - n_cli)])
    rng.shuffle(id_cliente)
    primeiro = pd.DataFrame({"id_cliente": id_cliente, "data_ativacao": data_ativ, "id_filial": id_filial, "id_plano": id_plano}) \
        .sort_values("data_ativacao").drop_duplicates("id_cliente")
    seg = planos.set_index("id_plano").loc[primeiro["id_plano"], "segmento"].to_numpy()
    pj = seg == "PJ"
    clientes = pd.DataFrame({
        "id_cliente": primeiro["id_cliente"].to_numpy(),
        "nome": [fake.company() if e else fake.name() for e in pj],
        "tipo": np.where(pj, "J", "F"),
        "documento_hash": [_hash_documento(fake.cnpj() if e else fake.cpf()) for e in pj],
        "bairro": [fake.bairro() for _ in range(len(primeiro))],
        "id_filial": primeiro["id_filial"].to_numpy(),
        "data_cadastro": [d - timedelta(days=int(x)) for d, x in zip(primeiro["data_ativacao"], rng.integers(0, 11, len(primeiro)))],
    }).sort_values("id_cliente")

    contratos = pd.DataFrame({
        "id_contrato": np.arange(1, n + 1),
        "id_cliente": id_cliente,
        "id_filial": id_filial,
        "id_plano": id_plano,
        "data_ativacao": data_ativ,
        "data_cancelamento": data_canc,
        "motivo_inclusao": motivo_inc,
        "motivo_cancelamento": motivo_canc,
        "valor_contrato": valor_contrato,
        "status": np.where(mes_canc >= 0, "D", "A"),   # código do ERP: A = ativo, D = desativado
    })

    # ---------- faturas: uma por competência, do mês da ativação ao mês da saída (ou de referência) ----------
    p_atraso = rng.beta(2, 8, n)          # propensão a pagar atrasado até 150 dias (média 20%)
    p_longo = rng.beta(1, 60, n)          # propensão a atraso longo, 60–200 dias (média ~1,6%)
    p_calote = rng.beta(1, 120, n)        # propensão a nunca pagar (média ~0,8%)
    linhas = []
    ref_mes = idx_mes[date(ref.year, ref.month, 1)]
    for i in range(n):
        ini = mes_ativ[i] + (1 if dia_ativ[i] > 25 else 0)
        fim = mes_canc[i] if mes_canc[i] >= 0 else ref_mes
        if fim < ini:
            continue
        financeiro = motivo_canc[i] == "DIFICULDADE FINANCEIRA"
        for j, m in enumerate(range(ini, fim + 1)):
            comp = meses_todos[m]
            venc = comp.replace(day=10)
            if venc > ref:
                continue
            u = rng.random()
            ultimas = financeiro and (fim - m) < 3
            # título nunca pago só sobrevive em contrato ativo se for recente: o antigo é negociado (85%) ou derruba o contrato
            calote = u < p_calote[i] and ((ref - venc).days <= 120 or rng.random() < 0.15)
            if ultimas or calote:
                pag, st = None, "A"
            elif u < p_calote[i] + p_longo[i]:
                pag = venc + timedelta(days=int(rng.integers(60, 201)))
                pag, st = (None, "A") if pag > ref else (pag, "R")
            elif u < p_calote[i] + p_longo[i] + p_atraso[i]:
                atraso = min(int(rng.geometric(1 / 12)), 150)
                pag = venc + timedelta(days=atraso)
                pag, st = (None, "A") if pag > ref else (pag, "R")
            else:
                pag, st = venc - timedelta(days=int(rng.integers(0, 10))), "R"
            linhas.append((i + 1, comp, venc, valor_contrato[i], pag, st))
    faturas = pd.DataFrame(linhas, columns=["id_contrato", "competencia", "data_vencimento", "valor", "data_pagamento", "status"])
    faturas.insert(0, "id_fatura", np.arange(1, len(faturas) + 1))
    faturas["data_emissao"] = faturas["data_vencimento"] - timedelta(days=10)
    # armadilha real: faturas canceladas ('C') existem e algumas carregam valor NEGATIVO — somar sem filtrar status erra o total
    canc = rng.random(len(faturas)) < 0.02
    faturas.loc[canc, "status"] = "C"
    faturas.loc[canc, "data_pagamento"] = None
    neg = canc & (rng.random(len(faturas)) < 0.3)
    faturas.loc[neg, "valor"] = -faturas.loc[neg, "valor"]

    # ---------- ordens de serviço ----------
    os_linhas = []
    vida_fim = np.array([d if d is not None else ref for d in data_canc], dtype=object)
    for i in range(n):
        a = data_ativ[i]
        ab = a - timedelta(days=int(rng.integers(1, 8)))
        os_linhas.append((i + 1, "INSTALACAO", ab, a, "F"))
        anos = max((vida_fim[i] - a).days, 1) / 365.25
        for assunto, taxa in (("REPARO", 0.40), ("MUDANCA DE ENDERECO", 0.05)):
            for _ in range(int(rng.poisson(taxa * anos))):
                ab = a + timedelta(days=int(rng.integers(0, max((vida_fim[i] - a).days, 1))))
                dur = float(rng.lognormal(0.4, 0.8))
                fe = ab + timedelta(days=dur)
                aberta = fe > ref or (ref - ab).days <= 10 and rng.random() < 0.3
                os_linhas.append((i + 1, assunto, ab, None if aberta else fe, "A" if aberta else "F"))
        if data_canc[i] is not None:
            ab = data_canc[i] - timedelta(days=int(rng.integers(0, 6)))
            os_linhas.append((i + 1, "CANCELAMENTO", ab, data_canc[i], "F"))
    ordens = pd.DataFrame(os_linhas, columns=["id_contrato", "assunto", "data_abertura", "data_fechamento", "status"])
    ordens = ordens.sort_values(["data_abertura", "id_contrato"]).reset_index(drop=True)
    ordens.insert(0, "id_os", np.arange(1, len(ordens) + 1))
    ordens["data_fechamento"] = ordens["data_fechamento"].map(lambda v: v.date() if isinstance(v, datetime) else v)

    # ---------- grava a extração como o ERP entregaria ----------
    C.STAGE.mkdir(parents=True, exist_ok=True)
    tabelas = {
        "filial": filiais, "plano": planos, "cliente": clientes, "contrato": contratos,
        "fatura": faturas, "ordem_servico": ordens,
    }
    colunas_data = {"cliente": ["data_cadastro"], "contrato": ["data_ativacao", "data_cancelamento"],
                    "fatura": ["competencia", "data_vencimento", "data_pagamento", "data_emissao"],
                    "ordem_servico": ["data_abertura", "data_fechamento"]}
    colunas_valor = {"plano": ["valor"], "contrato": ["valor_contrato"], "fatura": ["valor"]}
    contagens = {}
    for nome, df in tabelas.items():
        saida = df.copy()
        for c in colunas_data.get(nome, []):
            saida[c] = _para_erp_data(saida[c])
        for c in colunas_valor.get(nome, []):
            saida[c] = _para_erp_valor(saida[c])
        pasta = C.STAGE / nome
        pasta.mkdir(exist_ok=True)
        saida.to_csv(pasta / f"{nome}.csv", sep=";", index=False, encoding="utf-8")
        marcador = {"tabela": nome, "linhas": int(len(saida)), "geradoEm": datetime.now(timezone.utc).isoformat(),
                    "semente": C.SEMENTE, "dataReferencia": ref.isoformat()}
        (pasta / "_completa.json").write_text(json.dumps(marcador, ensure_ascii=False, indent=2), encoding="utf-8")
        contagens[nome] = int(len(saida))
    return contagens


if __name__ == "__main__":
    for t, q in gerar().items():
        print(f"{t:15s} {q:>8,d} linhas")
