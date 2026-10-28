-- SOT — calendário de meses do período analisado (até o mês da data de referência).
-- Toda série mensal nasce deste calendário: mês sem movimento aparece com zero, não some.
DROP TABLE IF EXISTS sot_calendario_mes;
CREATE TABLE sot_calendario_mes AS
WITH RECURSIVE m (dia_inicio) AS (
    SELECT date('__INICIO__')
    UNION ALL
    SELECT date(dia_inicio, '+1 month') FROM m WHERE date(dia_inicio, '+1 month') <= date('__REF__')
)
SELECT
    substr(dia_inicio, 1, 7)                 AS mes,
    dia_inicio,
    date(dia_inicio, '+1 month', '-1 day')   AS dia_fim
FROM m;
