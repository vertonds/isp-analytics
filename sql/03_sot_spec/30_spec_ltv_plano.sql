-- SPEC — LTV por plano, de duas formas que o leitor compara:
--   LTV esperado  = ticket médio recebido × vida esperada (1 ÷ churn mensal dos últimos 12 meses)
--   LTV esperado 60m = o mesmo, com a vida esperada LIMITADA a 60 meses (1 ÷ churn explode quando o churn é pequeno)
--   LTV realizado = receita recebida média dos contratos que JÁ SAÍRAM (perda de cliente)
-- Decisão documentada: o realizado é enviesado para baixo (só vê quem saiu, e quem fica mais tempo ainda não saiu).
DROP TABLE IF EXISTS spec_ltv_plano;
CREATE TABLE spec_ltv_plano AS
WITH ult12 AS MATERIALIZED (          -- materializada: sem isso o SQLite reavalia a CTE por linha e a consulta leva 30 s
    SELECT mes, dia_inicio, dia_fim FROM sot_calendario_mes ORDER BY mes DESC LIMIT 12
),
exposicao AS (
    SELECT c.id_plano,
           SUM(CASE WHEN c.data_ativacao < m.dia_inicio
                     AND (c.data_cancelamento IS NULL OR c.data_cancelamento >= m.dia_inicio) THEN 1 ELSE 0 END) AS ativos_inicio,
           SUM(CASE WHEN c.perda_cliente = 1
                     AND c.data_cancelamento BETWEEN m.dia_inicio AND m.dia_fim THEN 1 ELSE 0 END)                AS perdas
    FROM sot_contrato c
    CROSS JOIN ult12 m
    GROUP BY c.id_plano
),
ticket AS (
    SELECT c.id_plano, AVG(t.valor) AS ticket_medio
    FROM sot_titulo t JOIN sot_contrato c USING (id_contrato) JOIN ult12 u ON u.mes = t.competencia
    WHERE t.situacao = 'RECEBIDO'
    GROUP BY c.id_plano
),
realizado AS (
    SELECT c.id_plano,
           AVG(r.receita)           AS ltv_realizado,
           AVG(c.dias_de_casa) / 30.44 AS meses_de_casa,
           count(*)                 AS contratos_encerrados
    FROM sot_contrato c
    JOIN (SELECT id_contrato, SUM(valor) AS receita FROM sot_titulo WHERE situacao = 'RECEBIDO' GROUP BY id_contrato) r
      USING (id_contrato)
    WHERE c.perda_cliente = 1
    GROUP BY c.id_plano
)
SELECT p.id_plano, p.nome AS plano, p.segmento,
       ROUND(t.ticket_medio, 2)                                          AS ticket_medio,
       e.ativos_inicio                                                   AS exposicao_12m,
       e.perdas                                                          AS perdas_12m,
       ROUND(100.0 * e.perdas / NULLIF(e.ativos_inicio, 0), 2)           AS churn_mensal_pct,
       ROUND(1.0 * e.ativos_inicio / NULLIF(e.perdas, 0), 1)             AS vida_esperada_meses,
       ROUND(t.ticket_medio * e.ativos_inicio / NULLIF(e.perdas, 0), 2)  AS ltv_esperado,
       ROUND(t.ticket_medio * MIN(60.0, 1.0 * e.ativos_inicio / NULLIF(e.perdas, 0)), 2) AS ltv_esperado_60m,
       ROUND(r.ltv_realizado, 2)                                         AS ltv_realizado,
       ROUND(r.meses_de_casa, 1)                                         AS meses_de_casa_encerrados,
       r.contratos_encerrados
FROM sor_plano p
LEFT JOIN exposicao e USING (id_plano)
LEFT JOIN ticket    t USING (id_plano)
LEFT JOIN realizado r USING (id_plano)
ORDER BY p.id_plano;
