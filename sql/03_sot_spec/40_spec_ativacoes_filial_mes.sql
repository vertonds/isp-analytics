-- SPEC — ativações (vendas novas) por filial e mês, com as comparações que a tela mostra:
--   variação contra o mês anterior e contra o mesmo mês do ano anterior (janelas LAG), e a fatia da filial no mês.
-- Porta: ativações = vendas_novas da base mensal (o mesmo número em qualquer tela).
DROP TABLE IF EXISTS spec_ativacoes_filial_mes;
CREATE TABLE spec_ativacoes_filial_mes AS
SELECT mes, id_filial, filial,
       vendas_novas                                                                   AS ativacoes,
       LAG(vendas_novas, 1)  OVER (PARTITION BY id_filial ORDER BY mes)               AS mes_anterior,
       LAG(vendas_novas, 12) OVER (PARTITION BY id_filial ORDER BY mes)               AS mesmo_mes_ano_anterior,
       ROUND(100.0 * (vendas_novas - LAG(vendas_novas, 1) OVER (PARTITION BY id_filial ORDER BY mes))
             / NULLIF(LAG(vendas_novas, 1) OVER (PARTITION BY id_filial ORDER BY mes), 0), 1) AS var_mes_pct,
       ROUND(100.0 * (vendas_novas - LAG(vendas_novas, 12) OVER (PARTITION BY id_filial ORDER BY mes))
             / NULLIF(LAG(vendas_novas, 12) OVER (PARTITION BY id_filial ORDER BY mes), 0), 1) AS var_ano_pct,
       ROUND(100.0 * vendas_novas / NULLIF(SUM(vendas_novas) OVER (PARTITION BY mes), 0), 1)  AS fatia_pct
FROM sot_base_mensal
ORDER BY mes, id_filial;
