-- SPEC — safra (coorte) de vendas: de cada mês de venda, quantos continuam após 3, 6 e 12 meses.
--   «após N meses» só conta quem JÁ TEM N meses (elegíveis); coorte jovem fica com NULL, não com zero.
DROP TABLE IF EXISTS spec_safra_retencao;
CREATE TABLE spec_safra_retencao AS
WITH v AS (
    SELECT mes_ativacao, data_ativacao, data_cancelamento, perda_cliente
    FROM sot_contrato
    WHERE venda_nova = 1 AND data_ativacao >= '__INICIO__'
),
n AS (
    SELECT mes_ativacao, count(*) AS vendas,
           SUM(perda_cliente)     AS ja_cancelaram,
           SUM(CASE WHEN date(data_ativacao, '+3 months')  <= '__REF__' THEN 1 ELSE 0 END) AS eleg_3,
           SUM(CASE WHEN date(data_ativacao, '+3 months')  <= '__REF__'
                     AND (perda_cliente = 0 OR data_cancelamento >= date(data_ativacao, '+3 months'))  THEN 1 ELSE 0 END) AS ret_3,
           SUM(CASE WHEN date(data_ativacao, '+6 months')  <= '__REF__' THEN 1 ELSE 0 END) AS eleg_6,
           SUM(CASE WHEN date(data_ativacao, '+6 months')  <= '__REF__'
                     AND (perda_cliente = 0 OR data_cancelamento >= date(data_ativacao, '+6 months'))  THEN 1 ELSE 0 END) AS ret_6,
           SUM(CASE WHEN date(data_ativacao, '+12 months') <= '__REF__' THEN 1 ELSE 0 END) AS eleg_12,
           SUM(CASE WHEN date(data_ativacao, '+12 months') <= '__REF__'
                     AND (perda_cliente = 0 OR data_cancelamento >= date(data_ativacao, '+12 months')) THEN 1 ELSE 0 END) AS ret_12
    FROM v GROUP BY mes_ativacao
)
SELECT mes_ativacao AS safra, vendas, ja_cancelaram,
       ROUND(100.0 * ja_cancelaram / vendas, 1)      AS cancelados_pct,
       ROUND(100.0 * ret_3  / NULLIF(eleg_3, 0), 1)  AS retencao_3m_pct,
       ROUND(100.0 * ret_6  / NULLIF(eleg_6, 0), 1)  AS retencao_6m_pct,
       ROUND(100.0 * ret_12 / NULLIF(eleg_12, 0), 1) AS retencao_12m_pct
FROM n ORDER BY safra;
