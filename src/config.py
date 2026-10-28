"""Parâmetros do projeto — um lugar só. Nenhum outro módulo lê caminho, data ou volume por conta própria."""
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
STAGE = RAIZ / "data" / "stage"            # extração crua, como o ERP entregaria (CSV ; datas dd/mm/aaaa ; vírgula decimal)
WAREHOUSE = RAIZ / "data" / "warehouse"
BANCO = WAREHOUSE / "isp_analytics.db"   # SQLite: camadas SOR, SOT e SPEC por prefixo de tabela
SQL = RAIZ / "sql"
IMAGENS = RAIZ / "docs" / "imagens"
RESULTADOS = RAIZ / "docs" / "RESULTADOS.md"

SEMENTE = 42                               # reprodutível: mesma semente, mesma base
INICIO_HISTORICO = date(2021, 1, 1)        # a base já existia antes do período analisado
INICIO_PERIODO = date(2024, 1, 1)          # primeiro mês das séries (calendário do SOT)
DATA_REFERENCIA = date(2026, 9, 30)        # "hoje" da base: último dia fechado; nenhum cálculo usa a data real da máquina

N_CONTRATOS_HISTORICO = 3200               # ativados antes do período
N_CONTRATOS_PERIODO = 5800                 # ativados dentro do período
PROPORCAO_CLIENTES_COM_2_CONTRATOS = 0.12

FILIAIS = [
    (1, "Filial Centro"), (2, "Filial Norte"), (3, "Filial Sul"), (4, "Filial Leste"), (5, "Filial Oeste"),
]
PESO_FILIAL = [0.35, 0.20, 0.18, 0.15, 0.12]

# id, nome, velocidade (Mbps), mensalidade, segmento
PLANOS = [
    (1, "Fibra 200 Mega", 200, 89.90, "PF"),
    (2, "Fibra 400 Mega", 400, 109.90, "PF"),
    (3, "Fibra 600 Mega", 600, 129.90, "PF"),
    (4, "Fibra 1 Giga", 1000, 169.90, "PF"),
    (5, "Empresarial 500 Mega", 500, 249.90, "PJ"),
    (6, "Link Dedicado 100 Mega", 100, 899.90, "PJ"),
]
PESO_PLANO = [0.30, 0.30, 0.18, 0.10, 0.09, 0.03]

MOTIVOS_INCLUSAO = ["VENDA", "TROCA DE TITULARIDADE", "MIGRACAO DE PLANO"]
PESO_MOTIVO_INCLUSAO = [0.90, 0.06, 0.04]

MOTIVOS_CANCELAMENTO = [
    "DIFICULDADE FINANCEIRA", "MUDANCA DE ENDERECO", "CONCORRENCIA",
    "INSATISFACAO COM O SERVICO", "TROCA DE TITULARIDADE", "OUTROS",
]
PESO_MOTIVO_CANCELAMENTO = [0.28, 0.22, 0.20, 0.13, 0.08, 0.09]
SAIDAS_QUE_NAO_SAO_PERDA = ("TROCA DE TITULARIDADE",)   # o cliente continua na base com outro contrato

# risco mensal de cancelamento: base × filial × plano × idade do contrato
RISCO_MENSAL_BASE = 0.012
FATOR_RISCO_FILIAL = {1: 1.00, 2: 1.25, 3: 0.90, 4: 1.10, 5: 1.40}
FATOR_RISCO_PLANO = {1: 1.30, 2: 1.00, 3: 0.90, 4: 0.80, 5: 0.70, 6: 0.40}
FATOR_RISCO_IDADE = [(3, 2.3), (6, 1.6), (12, 1.15), (10_000, 0.85)]   # (até N meses, fator)

FAIXAS_ATRASO = ["01-30", "31-60", "61-90", "91-180", "181+"]
