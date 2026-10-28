-- Pergunta: quanto está vencido hoje, em quantos contratos, e como se distribui por idade do atraso?
-- Consolidado por faixa + linha TOTAL; a porta garante que as faixas somam o total vencido do SOT.
WITH por_faixa AS (
    SELECT ordem, faixa, SUM(titulos) AS titulos, SUM(contratos) AS contratos, ROUND(SUM(valor), 2) AS valor
    FROM spec_inadimplencia_faixa
    GROUP BY ordem, faixa
),
total AS (SELECT SUM(valor) AS valor FROM por_faixa)
SELECT f.ordem,
       f.faixa                                    AS faixa_dias,
       f.titulos,
       f.contratos,
       f.valor                                    AS valor_vencido,
       ROUND(100.0 * f.valor / t.valor, 1)        AS pct_do_vencido
FROM por_faixa f CROSS JOIN total t
UNION ALL
SELECT 9, 'TOTAL', SUM(titulos), SUM(contratos), ROUND(SUM(valor), 2), 100.0 FROM por_faixa
ORDER BY 1;
