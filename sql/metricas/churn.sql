-- Pergunta: como anda o churn por filial nos últimos 12 meses, e qual a tendência (média móvel de 3 meses)?
-- Lê o SPEC (regra escrita uma vez) e acrescenta só a leitura: janela móvel por filial.
WITH serie AS (
    SELECT mes, id_filial, filial, ativos_inicio, perdas, churn_pct,
           ROUND(AVG(churn_pct) OVER (PARTITION BY id_filial ORDER BY mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS media_movel_3m
    FROM spec_churn_mensal
)
SELECT mes, filial, ativos_inicio, perdas, churn_pct, media_movel_3m
FROM serie
WHERE mes > strftime('%Y-%m', date('__REF__', 'start of month', '-12 months'))
ORDER BY mes, id_filial;
