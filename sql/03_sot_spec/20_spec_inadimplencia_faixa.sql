-- SPEC — inadimplência por faixa de atraso na data de referência, por filial.
--   Título vencido = status 'A' com vencimento antes da referência (o SOT já tirou os 'C').
--   Coluna de valor usada: valor do título. Porta: a soma das faixas reproduz o total vencido.
DROP TABLE IF EXISTS spec_inadimplencia_faixa;
CREATE TABLE spec_inadimplencia_faixa AS
WITH faixas (faixa, ordem) AS (
    VALUES ('01-30', 1), ('31-60', 2), ('61-90', 3), ('91-180', 4), ('181+', 5)
),
vencidos AS (
    SELECT id_filial, faixa_atraso AS faixa,
           count(*)                      AS titulos,
           count(DISTINCT id_contrato)   AS contratos,
           ROUND(SUM(valor), 2)          AS valor
    FROM sot_titulo
    WHERE situacao = 'VENCIDO'
    GROUP BY id_filial, faixa_atraso
)
SELECT fx.ordem, fx.faixa, fl.id_filial, fl.nome AS filial,
       COALESCE(v.titulos, 0)   AS titulos,
       COALESCE(v.contratos, 0) AS contratos,
       COALESCE(v.valor, 0.0)   AS valor
FROM faixas fx
CROSS JOIN sor_filial fl
LEFT JOIN vencidos v ON v.faixa = fx.faixa AND v.id_filial = fl.id_filial
ORDER BY fl.id_filial, fx.ordem;
