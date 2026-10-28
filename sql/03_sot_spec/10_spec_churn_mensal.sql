-- SPEC — churn mensal por filial e consolidado.
--   churn % = perdas de cliente no mês ÷ contratos ativos no INÍCIO do mês (a base exposta ao risco).
--   id_filial 0 = TOTAL. A porta confere que o TOTAL é a soma das filiais.
DROP TABLE IF EXISTS spec_churn_mensal;
CREATE TABLE spec_churn_mensal AS
SELECT mes, id_filial, filial, ativos_inicio, perdas,
       ROUND(100.0 * perdas / NULLIF(ativos_inicio, 0), 2) AS churn_pct
FROM sot_base_mensal
UNION ALL
SELECT mes, 0, 'TOTAL', SUM(ativos_inicio), SUM(perdas),
       ROUND(100.0 * SUM(perdas) / NULLIF(SUM(ativos_inicio), 0), 2)
FROM sot_base_mensal
GROUP BY mes
ORDER BY mes, id_filial;
