-- SOT (Source of Truth) — contrato com as regras de negócio escritas UMA vez:
--   venda nova     = motivo de inclusão VENDA (troca de titularidade e migração não são venda);
--   perda de cliente = saída registrada cujo motivo NÃO é troca de titularidade (o cliente segue na base);
--   dias de casa   = da ativação até a saída, ou até a data de referência se ainda ativo.
-- Toda métrica de churn, safra e LTV lê estas colunas; ninguém reescreve a regra.
DROP TABLE IF EXISTS sot_contrato;
CREATE TABLE sot_contrato AS
SELECT
    c.id_contrato,
    c.id_cliente,
    c.id_filial,
    f.nome                                   AS filial,
    c.id_plano,
    p.nome                                   AS plano,
    p.segmento,
    c.valor_contrato,
    c.data_ativacao,
    substr(c.data_ativacao, 1, 7)            AS mes_ativacao,
    c.data_cancelamento,
    substr(c.data_cancelamento, 1, 7)        AS mes_saida,
    c.motivo_inclusao,
    c.motivo_cancelamento,
    CASE WHEN c.motivo_inclusao = 'VENDA' THEN 1 ELSE 0 END                                    AS venda_nova,
    CASE WHEN c.data_cancelamento IS NOT NULL
          AND c.motivo_cancelamento <> 'TROCA DE TITULARIDADE' THEN 1 ELSE 0 END               AS perda_cliente,
    CASE WHEN c.data_cancelamento IS NULL THEN 'ATIVO' ELSE 'CANCELADO' END                    AS situacao,
    CAST(julianday(COALESCE(c.data_cancelamento, '__REF__')) - julianday(c.data_ativacao) AS INTEGER) AS dias_de_casa
FROM sor_contrato c
JOIN sor_filial f USING (id_filial)
JOIN sor_plano  p USING (id_plano);

CREATE INDEX ix_sot_contrato_datas ON sot_contrato (data_ativacao, data_cancelamento);
