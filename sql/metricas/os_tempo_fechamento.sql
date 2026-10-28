-- Pergunta: quanto tempo leva para fechar uma O.S., por assunto, nos últimos 12 meses — e quantas seguem abertas?
--   Tempo só de O.S. FECHADA; abertas aparecem em coluna própria (ausência de fechamento não é tempo zero).
WITH janela AS (
    SELECT * FROM sor_ordem_servico
    WHERE data_abertura > date('__REF__', 'start of month', '-12 months')
),
fechadas AS (
    SELECT assunto, julianday(data_fechamento) - julianday(data_abertura) AS dias
    FROM janela WHERE status = 'F'
),
ordenadas AS (
    SELECT assunto, dias,
           ROW_NUMBER() OVER (PARTITION BY assunto ORDER BY dias) AS pos,
           count(*)     OVER (PARTITION BY assunto)               AS n
    FROM fechadas
)
SELECT f.assunto,
       count(*)                                        AS fechadas,
       (SELECT count(*) FROM janela j WHERE j.assunto = f.assunto AND j.status = 'A') AS abertas,
       ROUND(AVG(f.dias), 1)                           AS media_dias,
       ROUND((SELECT AVG(dias) FROM ordenadas o WHERE o.assunto = f.assunto AND o.pos IN ((o.n + 1) / 2, (o.n + 2) / 2)), 1) AS mediana_dias,
       ROUND(MAX(f.dias), 1)                           AS maximo_dias
FROM fechadas f
GROUP BY f.assunto
ORDER BY fechadas DESC;
