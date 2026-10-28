-- SOT — título (fatura) com o filtro de status aplicado ANTES de qualquer soma.
--   Entram só 'A' (aberta) e 'R' (recebida). 'C' (cancelada) nunca alimenta indicador — existem canceladas com
--   valor NEGATIVO: somar sem filtrar subestima o total.
--   Competência = mês do VENCIMENTO (nunca a emissão). Atraso conta a partir do vencimento até a data de referência.
DROP TABLE IF EXISTS sot_titulo;
CREATE TABLE sot_titulo AS
SELECT
    f.id_fatura,
    f.id_contrato,
    c.id_filial,
    c.id_plano,
    substr(f.data_vencimento, 1, 7)          AS competencia,
    f.data_vencimento,
    f.valor,
    f.status,
    f.data_pagamento,
    CASE WHEN f.status = 'R'                       THEN 'RECEBIDO'
         WHEN f.data_vencimento >= '__REF__'       THEN 'A VENCER'
         ELSE                                           'VENCIDO' END                               AS situacao,
    CASE WHEN f.status = 'R'
         THEN MAX(0, CAST(julianday(f.data_pagamento) - julianday(f.data_vencimento) AS INTEGER))
         ELSE MAX(0, CAST(julianday('__REF__')       - julianday(f.data_vencimento) AS INTEGER)) END AS dias_atraso,
    CASE WHEN f.status <> 'A' OR f.data_vencimento >= '__REF__' THEN NULL
         WHEN julianday('__REF__') - julianday(f.data_vencimento) <= 30  THEN '01-30'
         WHEN julianday('__REF__') - julianday(f.data_vencimento) <= 60  THEN '31-60'
         WHEN julianday('__REF__') - julianday(f.data_vencimento) <= 90  THEN '61-90'
         WHEN julianday('__REF__') - julianday(f.data_vencimento) <= 180 THEN '91-180'
         ELSE '181+' END                                                                            AS faixa_atraso
FROM sor_fatura f
JOIN sor_contrato c USING (id_contrato)
WHERE f.status IN ('A', 'R');

CREATE INDEX ix_sot_titulo_sit ON sot_titulo (situacao, faixa_atraso);
CREATE INDEX ix_sot_titulo_contrato ON sot_titulo (id_contrato);
