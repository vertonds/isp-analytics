-- Pergunta: as vendas recentes estão ficando mais ou menos tempo do que as antigas?
SELECT safra, vendas, ja_cancelaram, cancelados_pct, retencao_3m_pct, retencao_6m_pct, retencao_12m_pct
FROM spec_safra_retencao
ORDER BY safra;
