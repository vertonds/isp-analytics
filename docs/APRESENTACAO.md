# Apresentação do ISP Analytics na identidade "Placar" (branch `apresentacao`)

Só apresentação: nenhuma regra de negócio, SQL ou número mudou. A cada fase o pipeline e os testes rodam de novo.

## Fase 1 — Gráficos (28/10/2026)

### O que mudou

- `src/relatorio.py` gera **duas versões de cada gráfico**: `<nome>-claro.png` (fundo creme `#FDFAF3`) e
  `<nome>-escuro.png` (fundo grafite `#1C1922`). As cinco imagens antigas de versão única saíram.
- **README.md e RESULTADOS.md** usam `<picture>` com `prefers-color-scheme: dark`: o GitHub mostra a versão
  que combina com o tema de quem lê.
- **Fontes:** Reddit Sans nos títulos e textos, JetBrains Mono em números, datas e eixos. Instâncias estáticas
  (Regular e Bold), subconjunto latino, em `docs/fontes/` com as licenças OFL. O matplotlib as registra em tempo
  de execução; sem elas, cai na fonte padrão.
- **Linha "Total" em dourado:** `#E8B23A` no escuro (9,0:1) e `#8A6508` no claro (5,1:1), mais grossa.
- **Filiais:** paleta categórica validada pelo script do guia de visualização (separação para daltonismo
  ΔE ≥ 8 entre vizinhas, contraste ≥ 3:1 sobre o fundo nas duas versões). Sem tons de ocre/amarelo nas
  filiais, para nenhuma se confundir com o dourado do Total.

  | Versão | Centro | Norte | Sul | Leste | Oeste | Total |
  |---|---|---|---|---|---|---|
  | clara | `#2a78d6` | `#d9541e` | `#0f8a68` | `#6250d6` | `#c2457a` | `#8A6508` |
  | escura | `#3987e5` | `#d95926` | `#199e70` | `#9085e9` | `#d55181` | `#E8B23A` |

- **Inadimplência:** rampa ordinal roxa de 5 passos (clara `#B89BE0 → #3D1A66`, escura `#6B3FA8 → #E0D3F3`),
  passo mais claro ≥ 2:1 sobre o fundo. Grade atrás das barras.
- **LTV:** esperado em dourado, realizado em roxo. **Safra:** 3 meses em cinza, 6 em roxo, 12 em dourado.
- **Rótulos no fim das linhas** do churn: função `_espalhar` afasta os que ficariam sobrepostos (gap mínimo de
  5,5 % da escala), mantendo a ordem; "Total" em negrito e na cor da linha.
- **Títulos coerentes com o período:** o churn diz "out/2024 a set/2026 (24 meses)", as ativações
  "abr/2025 a set/2026 (18 meses)", a safra "safras de jan/2024 a set/2026", tudo calculado dos dados.

### Conferido

- Pipeline completo e 9 testes: OK, antes e depois.
- `git diff docs/RESULTADOS.md`: nenhuma linha de tabela de métrica mudou (só a data de geração e os tempos
  de execução).
- Contraste calculado para cada cor de linha/barra sobre cada fundo (todos ≥ 3:1) e paleta validada nas duas
  versões.

### Peso no repositório

`docs/fontes/` 260 KB · `docs/imagens/` 976 KB (10 PNG a 130 dpi).

### Ajustes pedidos na aprovação da Fase 1 (feitos)

1. Gráfico de churn sem legenda: os rótulos no fim das linhas identificam as séries e a legenda cobria os picos.
2. Quantidade de meses nos títulos do churn e das ativações vem de `len(meses)`, não de texto fixo.
3. **Anotado para a Fase 3:** os títulos das seções do RESULTADOS.md dizem "últimos 12 meses" (a tabela), mas os
   gráficos de churn e ativações mostram 24 e 18 meses. Deixar explícito o período do gráfico e o da tabela.

Também: a frase do README §6 dizia "base crescendo de 2.415 para 6.195 no período" logo após "últimos 12 meses";
2.415 é o início da série de 33 meses (no início dos últimos 12 são 4.678). A frase agora diz os dois períodos.

## Fase 2 — README (28/10/2026)

- **Resumo em 30 segundos** logo depois dos selos: uma frase do que é o projeto, link do portfólio, três números
  conferidos na base (churn 1,3 % ao mês nos últimos 12 meses com a base de 4.678 para 6.195 ativos; R$ 443.842
  vencidos, 59,7 % há mais de 180 dias; 6 portas + 9 testes) e o gráfico de churn em `<picture>`.
- **Índice** em uma linha, com âncoras conferidas contra os títulos das 9 seções, mais o link para o RESULTADOS.
- **Diagrama de arquitetura em Mermaid** no lugar do desenho em texto: fluxo ERP → Stage → SOR → SOT → SPEC →
  Consultas, com as três portas em hexágonos ligados por linha pontilhada à etapa que elas liberam. Cores da
  identidade (roxo profundo com borda dourada nas camadas, dourado lavado nas portas). Nos rótulos só `<br/>`,
  que o GitHub renderiza; sem outras tags HTML.
- Link do portfólio também na seção Sobre.
- Nenhuma regra, SQL ou número mudou. Pipeline e testes: OK.

A conferir depois do push: o Mermaid renderizado no GitHub e a troca claro/escuro do `<picture>` (se o GitHub
não trocar com caminho relativo, usar o endereço completo da imagem no repositório).

### Ajustes pedidos na aprovação da Fase 2 (feitos)

1. Seção Sobre: "outubro de 2026" no lugar de "nov–dez/2026".
2. Leitura das ativações: conferido na base, 5.200 é a série de 33 meses, 3.187 os 18 meses do gráfico e 2.168 os
   12 da tabela; a Filial Centro fica em ~34% em qualquer recorte (o "~32%" estava errado). A frase diz os três.
3. Citação do topo enxuta: só a frase de que todo dado é sintético e nenhum dado da empresa está no repositório.
4. Saída de exemplo do pipeline atualizada com uma execução atual.
5. Porcentagens sem espaço antes do % em todo o README.

## Fase 3 — RESULTADOS.md (28/10/2026)

- **Períodos explícitos** na linha abaixo de cada título: "gráfico: últimos 24 meses · tabela: últimos 12 meses"
  no churn, "gráfico: últimos 18 meses · tabela: últimos 12 meses" nas ativações, a data de referência nas
  inadimplências, e assim por diante. Os números de meses vêm dos dados.
- **Uma ou duas frases de leitura por métrica, calculadas na hora** (`_leituras` em `src/relatorio.py`): as mesmas
  consultas da tabela alimentam a frase, então ela nunca diz algo que a tabela não mostre e se atualiza sozinha
  se a base mudar. Exemplos: churn médio dos 12 meses com a filial de maior e menor churn; vencido total, parcela
  acima de 180 dias e parcela em contratos já cancelados; LTV mínimo e máximo e razão realizado/esperado; vendas
  nos três recortes; retenção média por idade; mediana e média do reparo nas O.S.
- **Tabelas longas recolhidas** em `<details>`: churn (72 linhas) e safra (33 linhas). As curtas ficam abertas.
- Índice no topo do RESULTADOS.
- Nenhuma regra, SQL ou número mudou: as frases só leem o que já estava nas tabelas. Pipeline e testes: OK.

### Ajustes pedidos na aprovação da Fase 3 (feitos)

1. **Inadimplência: 1.776 × 1.992.** A linha TOTAL da tabela soma a coluna `contratos` das faixas (um contrato com
   títulos em mais de uma faixa conta em cada uma); os contratos distintos com vencido são 1.776. Nesta branch, só
   apresentação: nota abaixo da tabela no RESULTADOS (calculada) e no README.
   **Próximo passo, em branch separada (muda regra):** no `sql/metricas/inadimplencia_faixas.sql`, a linha TOTAL
   passa a contar `COUNT(DISTINCT id_contrato)` do `sot_titulo` vencido, com um teste novo que compare o TOTAL com
   a contagem distinta; avaliar se o `spec_inadimplencia_faixa` precisa expor a contagem distinta também.
2. **Churn, README:** "Norte e Oeste oscilam mais porque são as menores" não conferia (as menores são Oeste, Leste e
   Norte). A frase agora usa o desvio padrão do churn mensal nos 24 meses do gráfico: Oeste 0,63 pp (542 ativos em
   média), Leste 0,44 (728), Norte 0,43 (829), Centro 0,26 (1.640).
3. **LTV:** em vez de "24% somando os planos", a faixa por plano, calculada: o realizado fica entre 23% e 27% do
   esperado em cada plano (RESULTADOS calculado; README com os mesmos valores).
4. **Execução registrada:** só as etapas da última execução do pipeline (do `carregar_sor` que precede as últimas
   `portas` até elas), em vez dos últimos 6 registros, que misturavam as cargas dos testes.

## Fase 4 — Repositório (28/10/2026)

- **Imagem de prévia** `docs/imagens/social-preview.png`, 1280 × 640, na identidade: nome do projeto, frase curta,
  quatro números que descrevem o projeto (4 camadas, 5 métricas, 6 portas, 9 testes) e um traçado abstrato de
  linhas, sem dados reais. Para subir: GitHub → repositório → **Settings → General → Social preview → Edit → Upload**.
- **Campo Website do About** e **release v1.0**: comandos abaixo, para rodar depois de publicar a branch na `main`.

```powershell
cd <pasta-local-do-repositorio>

# 1) publicar (commit e push são seus; sem Co-authored-by)
git add -A
git commit -m "Apresentacao: graficos claro/escuro na identidade do portfolio, README com Mermaid e resumo, RESULTADOS com leituras calculadas"
git checkout main
git merge --ff-only apresentacao
git push

# 2) About: site, descrição e tópicos
gh repo edit vertonds/isp-analytics --homepage "https://vertonds.github.io" --description "Pipeline analitico de um provedor de internet (dados sinteticos): camadas Stage > SOR > SOT > SPEC em SQLite, metricas em SQL, portas de qualidade e CI" --add-topic analytics-engineering --add-topic sql --add-topic python --add-topic sqlite --add-topic data-quality --add-topic portfolio

# 3) release v1.0 (cria a tag no commit atual da main)
gh release create v1.0 --title "v1.0 — ISP Analytics" --notes "Primeira versao publica: base sintetica, camadas Stage/SOR/SOT/SPEC em SQLite, metricas em SQL (churn, inadimplencia, LTV, ativacoes, safra, O.S.), portas de qualidade, testes e CI. Graficos em versao clara e escura, README com diagrama Mermaid e RESULTADOS com leituras calculadas dos dados."
```

Depois do push, conferir no GitHub: o Mermaid renderizado no README, a troca claro/escuro do `<picture>` (abrir o
README e o RESULTADOS no tema escuro; se vier a versão clara, trocar os caminhos relativos pelo endereço completo
da imagem), o selo do CI verde e a release na barra lateral.
