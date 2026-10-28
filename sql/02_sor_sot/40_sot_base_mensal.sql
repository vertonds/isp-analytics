-- SOT — fluxo da base por mês e filial: UMA conta só para o saldo.
--   ativos_inicio: ativados antes do 1º dia e sem saída antes dele
--   entradas / saídas: todo movimento do mês (inclui troca de titularidade)
--   vendas_novas / perdas: só o que a regra do contrato classifica como venda e como perda
-- Invariante (porta): ativos_fim = ativos_inicio + entradas − saídas, e o fim de um mês é o início do seguinte.
DROP TABLE IF EXISTS sot_base_mensal;
CREATE TABLE sot_base_mensal AS
SELECT
    m.mes,
    m.dia_inicio,
    m.dia_fim,
    f.id_filial,
    f.nome AS filial,
    (SELECT count(*) FROM sot_contrato c
      WHERE c.id_filial = f.id_filial AND c.data_ativacao < m.dia_inicio
        AND (c.data_cancelamento IS NULL OR c.data_cancelamento >= m.dia_inicio))             AS ativos_inicio,
    (SELECT count(*) FROM sot_contrato c
      WHERE c.id_filial = f.id_filial AND c.data_ativacao BETWEEN m.dia_inicio AND m.dia_fim)  AS entradas,
    (SELECT count(*) FROM sot_contrato c
      WHERE c.id_filial = f.id_filial AND c.data_ativacao BETWEEN m.dia_inicio AND m.dia_fim
        AND c.venda_nova = 1)                                                                  AS vendas_novas,
    (SELECT count(*) FROM sot_contrato c
      WHERE c.id_filial = f.id_filial AND c.data_cancelamento BETWEEN m.dia_inicio AND m.dia_fim) AS saidas,
    (SELECT count(*) FROM sot_contrato c
      WHERE c.id_filial = f.id_filial AND c.data_cancelamento BETWEEN m.dia_inicio AND m.dia_fim
        AND c.perda_cliente = 1)                                                               AS perdas,
    (SELECT count(*) FROM sot_contrato c
      WHERE c.id_filial = f.id_filial AND c.data_ativacao <= m.dia_fim
        AND (c.data_cancelamento IS NULL OR c.data_cancelamento > m.dia_fim))                 AS ativos_fim
FROM sot_calendario_mes m
CROSS JOIN sor_filial f
ORDER BY m.mes, f.id_filial;
