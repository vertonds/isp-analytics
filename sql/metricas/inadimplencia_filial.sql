-- Pergunta: qual filial carrega mais atraso, em valor e em proporção da sua base ativa?
--   taxa = contratos ativos com algum título vencido ÷ contratos ativos da filial.
WITH ativos AS (
    SELECT id_filial, count(*) AS contratos_ativos FROM sot_contrato WHERE situacao = 'ATIVO' GROUP BY id_filial
),
vencido AS (
    SELECT t.id_filial,
           count(DISTINCT t.id_contrato)               AS contratos_vencidos,
           ROUND(SUM(t.valor), 2)                      AS valor_vencido,
           ROUND(SUM(CASE WHEN t.faixa_atraso IN ('91-180', '181+') THEN t.valor ELSE 0 END), 2) AS valor_acima_90d
    FROM sot_titulo t JOIN sot_contrato c USING (id_contrato)
    WHERE t.situacao = 'VENCIDO' AND c.situacao = 'ATIVO'
    GROUP BY t.id_filial
)
SELECT f.nome AS filial, a.contratos_ativos, v.contratos_vencidos,
       ROUND(100.0 * v.contratos_vencidos / a.contratos_ativos, 1) AS taxa_inadimplencia_pct,
       v.valor_vencido, v.valor_acima_90d,
       RANK() OVER (ORDER BY 1.0 * v.contratos_vencidos / a.contratos_ativos DESC) AS posicao
FROM sor_filial f JOIN ativos a USING (id_filial) JOIN vencido v USING (id_filial)
ORDER BY posicao;
