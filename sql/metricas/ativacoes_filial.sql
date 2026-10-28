-- Pergunta: quantas vendas novas cada filial fez nos últimos 12 meses, e como foi o último mês fechado?
WITH ultimos AS (
    SELECT * FROM spec_ativacoes_filial_mes
    WHERE mes > strftime('%Y-%m', date('__REF__', 'start of month', '-12 months'))
),
ultimo_mes AS (SELECT MAX(mes) AS mes FROM ultimos)
SELECT u.filial,
       SUM(u.ativacoes)                                              AS ativacoes_12m,
       ROUND(AVG(u.ativacoes), 1)                                    AS media_mensal,
       MAX(CASE WHEN u.mes = um.mes THEN u.ativacoes END)            AS ultimo_mes,
       MAX(CASE WHEN u.mes = um.mes THEN u.var_mes_pct END)          AS var_vs_mes_anterior_pct,
       MAX(CASE WHEN u.mes = um.mes THEN u.var_ano_pct END)          AS var_vs_ano_anterior_pct,
       MAX(CASE WHEN u.mes = um.mes THEN u.fatia_pct END)            AS fatia_no_ultimo_mes_pct,
       RANK() OVER (ORDER BY SUM(u.ativacoes) DESC)                  AS posicao
FROM ultimos u CROSS JOIN ultimo_mes um
GROUP BY u.id_filial, u.filial
ORDER BY posicao;
