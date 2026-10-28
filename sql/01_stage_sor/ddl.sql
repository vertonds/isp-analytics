-- SOR (System of Record): cópia tipada da extração. Chaves declaradas, nenhuma regra de negócio.
-- Datas em ISO (aaaa-mm-dd), valores em REAL, códigos de status como o ERP entrega.

CREATE TABLE IF NOT EXISTS sor_filial (
    id_filial   INTEGER PRIMARY KEY,
    nome        TEXT NOT NULL,
    cidade      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sor_plano (
    id_plano        INTEGER PRIMARY KEY,
    nome            TEXT NOT NULL,
    velocidade_mbps INTEGER NOT NULL,
    valor           REAL NOT NULL,
    segmento        TEXT NOT NULL             -- PF | PJ
);

CREATE TABLE IF NOT EXISTS sor_cliente (
    id_cliente      INTEGER PRIMARY KEY,
    nome            TEXT NOT NULL,
    tipo            TEXT NOT NULL,            -- F (pessoa física) | J (jurídica)
    documento_hash  TEXT NOT NULL,            -- só o resumo do CPF/CNPJ persiste
    bairro          TEXT,
    id_filial       INTEGER NOT NULL REFERENCES sor_filial (id_filial),
    data_cadastro   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sor_contrato (
    id_contrato         INTEGER PRIMARY KEY,
    id_cliente          INTEGER NOT NULL REFERENCES sor_cliente (id_cliente),
    id_filial           INTEGER NOT NULL REFERENCES sor_filial (id_filial),
    id_plano            INTEGER NOT NULL REFERENCES sor_plano (id_plano),
    data_ativacao       TEXT NOT NULL,
    data_cancelamento   TEXT,
    motivo_inclusao     TEXT NOT NULL,        -- VENDA | TROCA DE TITULARIDADE | MIGRACAO DE PLANO
    motivo_cancelamento TEXT,
    valor_contrato      REAL NOT NULL,
    status              TEXT NOT NULL         -- A (ativo) | D (desativado)
);
CREATE INDEX IF NOT EXISTS ix_sor_contrato_datas ON sor_contrato (data_ativacao, data_cancelamento);

CREATE TABLE IF NOT EXISTS sor_fatura (
    id_fatura       INTEGER PRIMARY KEY,
    id_contrato     INTEGER NOT NULL REFERENCES sor_contrato (id_contrato),
    competencia     TEXT NOT NULL,
    data_vencimento TEXT NOT NULL,
    valor           REAL NOT NULL,
    data_pagamento  TEXT,
    status          TEXT NOT NULL,            -- A (aberta) | R (recebida) | C (cancelada — nunca entra em indicador)
    data_emissao    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_sor_fatura_contrato ON sor_fatura (id_contrato);
CREATE INDEX IF NOT EXISTS ix_sor_fatura_venc ON sor_fatura (data_vencimento, status);

CREATE TABLE IF NOT EXISTS sor_ordem_servico (
    id_os           INTEGER PRIMARY KEY,
    id_contrato     INTEGER NOT NULL REFERENCES sor_contrato (id_contrato),
    assunto         TEXT NOT NULL,            -- INSTALACAO | REPARO | MUDANCA DE ENDERECO | CANCELAMENTO
    data_abertura   TEXT NOT NULL,
    data_fechamento TEXT,
    status          TEXT NOT NULL             -- A (aberta) | F (fechada)
);
CREATE INDEX IF NOT EXISTS ix_sor_os_contrato ON sor_ordem_servico (id_contrato);
