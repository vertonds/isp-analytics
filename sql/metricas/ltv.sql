-- Pergunta: quanto vale um cliente de cada plano, e o esperado bate com o que já se realizou?
SELECT plano, segmento, ticket_medio, churn_mensal_pct, vida_esperada_meses, ltv_esperado, ltv_esperado_60m,
       ltv_realizado, meses_de_casa_encerrados, contratos_encerrados,
       RANK() OVER (ORDER BY ltv_esperado_60m DESC) AS posicao
FROM spec_ltv_plano
ORDER BY posicao;
