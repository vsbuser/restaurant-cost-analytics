# Registro de decisões técnicas (ADR simplificado)

Formato: **o quê / por quê / alternativas descartadas**.

---

## 2026-07-09 — Extração de notas com VLM local via Ollama

- **O quê:** extração foto → JSON usa modelo de visão local (Ollama + Qwen2.5-VL ou MiniCPM-V), exposto por um backend FastAPI. Claude API como alternativa plugável via `extractor.py`.
- **Por quê:** sem custo por requisição, sem dependência externa, demonstra ML engineering no portfólio.
- **Alternativas descartadas:** só API externa (custo + menos aprendizado); OCR tradicional (Tesseract — frágil para notas variadas).
- **Trade-off aceito:** Streamlit Cloud não roda o VLM; demo pública usará a via API como fallback.

## 2026-07-09 — App mobile via navegador (sem app nativo)

- **O quê:** Streamlit responsivo + atalho na tela inicial; câmera via `st.camera_input()`.
- **Por quê:** stack que já domino, um único codebase, entrega mais rápida.
- **Alternativas descartadas:** app nativo / React Native (custo de aprendizado fora do foco DA/DS).

## 2026-07-10 — Raiz do repositório

- **O quê:** pasta local `RESTAURAPP` é a raiz do repo; nome no GitHub: `restaurant-cost-analytics`.

## 2026-07-10 — Schema SQL (Etapa 1)

- **O quê:** schema dedicado `restaurant` no Postgres/Supabase, com 7 tabelas (`fornecedores`, `produtos`, `notas_fiscais`, `nota_linhas`, `receitas`, `receita_ingredientes`, `vendas`). Preço fica em `nota_linhas.preco_unitario`, nunca em `produtos` — é histórico, usado depois para preço médio ponderado e custo dinâmico de receita.
- **Por quê:** normalização (evitar dependência transitiva do preço em relação ao produto) e para preservar o histórico de variação de preço por compra, que é a base das métricas de food cost e alerta de fornecedor.
- **Alternativas descartadas:** tabelas de lookup separadas para `unidade_medida` e `fonte` de nota — trocado por `CHECK` constraints para simplificar o MVP; revisar se a lista de valores crescer muito.
- **Trade-off aceito:** `unidade_medida` e `fonte` fixos via `CHECK` limitam flexibilidade, mas evitam overhead de tabelas extras nesta fase.

## 2026-07-10 — Gerador de dados sintéticos (Etapa 2)

- **O quê:** `scripts/generate_synthetic.py` conecta direto no Postgres via `psycopg2` (não via `supabase-py`) e usa `execute_values` para inserir `nota_linhas` e `vendas` em lote. Preço por compra segue um modelo multiplicativo (`preço_base × inflação × sazonalidade × fator_fornecedor × ruído log-normal`); vendas diárias por receita seguem Poisson com fator de dia da semana e crescimento mensal.
- **Por quê:** conexão direta é mais rápida para carga em lote de milhares de linhas do que passar pela API REST do Supabase; modelo multiplicativo e Poisson são as escolhas estatísticas corretas para, respectivamente, série de preços (variação percentual) e contagem de eventos por período.
- **Alternativas descartadas:** `Faker` para nomes de fornecedores/produtos — descartado em favor de uma lista curada de domínio (hospitality), mais realista para o portfólio do que nomes genéricos.
- **Trade-off aceito:** o script tem um flag `--reset` que faz `TRUNCATE ... CASCADE` nas tabelas de dados antes de regerar — destrutivo por design, mas necessário para reprodutibilidade (mesma seed, mesmo resultado).

## 2026-07-10 — App base: CRUD de notas fiscais (Etapa 3)

- **O quê:** `app/services/database.py` conecta direto no Postgres via `psycopg2` (pool de conexões), não via `supabase-py`. Formulário de nova nota (`app/components/forms.py`) usa uma lista incremental construída com `st.session_state` (adicionar/remover item), em vez de uma grade `st.data_editor`.
- **Por quê:** a API REST do Supabase só expõe por padrão os schemas `public`/`graphql_public` — nosso schema `restaurant` não seria visível por ali sem reconfigurar a exposição da API e lidar com Row Level Security; conexão direta evita essa complexidade. A lista incremental empilha os campos verticalmente, o que funciona melhor em tela de celular do que uma tabela larga editável — atende ao critério da etapa de registrar uma nota "inclusive pelo celular".
- **Alternativas descartadas:** `st.data_editor` com `num_rows="dynamic"` para os itens da nota — mais rápido de implementar, mas ruim em tela estreita e mais difícil de validar linha a linha.
- **Trade-off aceito:** sem exclusão (delete) de fornecedores/produtos nesta etapa — evita lidar com violação de FK (produtos/fornecedores já referenciados por notas), e não é um critério da etapa.

## 2026-07-10 — Fichas técnicas e food cost (Etapa 4)

- **O quê:** `sql/views.sql` cria 3 views encadeadas: `vw_ultimo_preco_produto` (window function `ROW_NUMBER() OVER (PARTITION BY produto_id ORDER BY data DESC)` para achar a compra mais recente de cada produto), `vw_custo_receita` (soma ingrediente × último preço) e `vw_food_cost` (% + semáforo via `CASE`). O custo é comparado direto contra `preco_venda` da receita — sem dividir por `porcoes`, porque as quantidades em `receita_ingredientes` já representam o prato inteiro como vendido (não por porção individual); `porcoes` é só informativo (quantas pessoas o prato rende).
- **Por quê:** window function é a ferramenta certa para "última linha por grupo" em SQL — mais portável que o `DISTINCT ON` específico do Postgres, e é o que o roadmap pede para aprender nesta etapa.
- **Bug encontrado e corrigido:** `app/services/database.py` devolvia ao pool (`ThreadedConnectionPool`) até uma conexão que já tinha morrido do lado do servidor (o pooler do Supabase encerra conexões ociosas), travando a app inteira até reiniciar o processo. Corrigido com um "ping" (`SELECT 1`) antes de entregar a conexão, descartando-a (`close=True`) e pegando outra do pool se falhar, e descartando também se a conexão falhar durante o uso.
- **Trade-off aceito:** o ping adiciona um round-trip extra por chamada ao banco — aceitável para o volume desta app (uso pessoal/portfólio, não alta concorrência).

## 2026-07-13 — Dashboard analítico (Etapa 5)

- **O quê:** `sql/views.sql` ganha `vw_preco_medio_mensal` (preço médio ponderado por produto/mês) e `vw_variacao_preco` (compara a compra mais recente de cada produto com a anterior via window function, `alerta = true` se subir mais de 10%). `app/pages/5_Dashboard.py` traz 5 gráficos Plotly, cada um com a cor escolhida pelo *job* dos dados, não por padrão: food cost por prato usa cor de **status** (verde/amarelo/vermelho, é estado); variação de preço usa **emphasis** (vermelho só no insumo que dispara o alerta, cinza no resto — "esse aqui subiu", não uma comparação de identidades); evolução de preço mensal usa paleta **categórica** fixa (cada insumo é uma identidade); gasto por fornecedor e receita por categoria usam **sequencial** de um hue só (é comparação de magnitude, não identidade).
- **Por quê:** a cor tem que carregar o significado certo — usar cores diferentes para cada fornecedor num gráfico de ranking (magnitude) sugere identidade importa quando não importa; usar arco-íris em tudo é o erro mais comum em dashboard. Seguido o método da skill `dataviz` do Claude Code.
- **Alternativas descartadas:** gráfico de pizza para receita por categoria de menu — rejeitado a favor de barra horizontal (comparação de magnitude é mais fácil de ler em barra do que em ângulo/área).
- **Trade-off aceito:** os gráficos Plotly foram estilizados só para o tema claro (superfície `#fcfcfb`); não implementei uma variante para dark mode do Streamlit — escopo aceitável para portfólio pessoal.

## 2026-07-13 — Identidade visual "Kitchen Fresh"

- **O quê:** apresentadas 3 direções visuais completas (protótipo HTML comparativo) — "Ledger" (serifada/latão/escura, herança de bistrô), "Control Tower" (grotesca/azul/densa, estilo Tableau/PowerBI) e "Kitchen Fresh" (verde/arredondada/geométrica, tom food-tech como a Haddock). Escolhida **Kitchen Fresh**. Aplicada em `.streamlit/config.toml` (tema verde `#1e8f5e`) e `app/components/theme.py` (CSS compartilhado: sidebar verde-escuro, cards de KPI com borda colorida, tipografia Poppins nos títulos, botões/abas arredondados). Nome do app mantido: `RestaurApp`.
- **Por quê:** cor tem que carregar o significado certo (ver decisão da Etapa 5) — ao trocar a paleta de marca, as cores sequenciais dos gráficos de magnitude (`SEQ_BLUE` → `SEQ_GREEN`) e as cores de status (verde/amarelo/vermelho) foram atualizadas junto para não ficar com uma marca verde e gráficos em azul genérico.
- **Alternativas descartadas:** Ledger e Control Tower, descartadas pela escolha do usuário em favor do tom mais próximo da referência Haddock.
- **Trade-off aceito:** a paleta foi implementada só para tema claro do Streamlit; `st.dataframe`/`st.data_editor` usam renderização interna (glide-data-grid) que aplica a `primaryColor` do tema ao texto das células — não é customizável via CSS (é canvas, não DOM), então o texto das tabelas herda um tom esverdeado. Aceitável: ainda legível, e reforça a identidade.

## 2026-07-13 — Extração de notas por foto (Etapa 6, em andamento)

- **O quê:** Ollama instalado localmente + modelo `minicpm-v` (~5.5GB) baixado — um dos dois candidatos do roadmap (o outro, `qwen2.5-vl`, fica pendente de teste). `backend/preprocessing.py` (correção de perspectiva via maior contorno + `warpPerspective`, CLAHE para contraste, resize), `backend/vision.py` (chama `/api/generate` do Ollama com `format: "json"`) e `backend/main.py` (FastAPI, endpoint `POST /extract`) implementados. `app/services/extractor.py` traz a abstração com dois provedores (`ollama` local via HTTP para o backend, ou `claude` direto via SDK Anthropic com `output_config.format` de schema JSON) — trocável por `EXTRACTOR_PROVIDER` no `.env`. Nova aba "Tirar foto" em `app/pages/3_Notas.py` com `st.camera_input()` (+ fallback `st.file_uploader()`), tela de validação humana antes de salvar (fonte `foto_ia`).
- **Bug real encontrado e corrigido:** o `format: "json"` do Ollama garante JSON *válido*, mas não garante os *tipos* do schema — o MiniCPM-V devolveu preços como texto formatado (`"R$ 6,20"`) em vez de número, o que quebraria a conversão para `float` na tela de validação. Corrigido com uma função de sanitização (`_para_numero`) em `backend/vision.py` que lê tanto números quanto texto em formato de moeda brasileiro (vírgula decimal, símbolo R$) antes de retornar.
- **Validado:** teste de ponta a ponta com uma nota fiscal sintética (gerada via PIL) via `curl` direto no endpoint `/extract` — fornecedor, itens, quantidades, preços e total extraídos corretamente após a correção. Inferência em CPU (sem GPU) levou ~45s já com o modelo carregado em memória (~50s incluindo o load a frio na primeira chamada).
- **Pendente para a próxima sessão:** testar o fluxo completo pela UI do Streamlit (aba "Tirar foto"); decidir sobre upload da foto original para o Supabase Storage (mencionado no roadmap, ainda não implementado — por ora só os dados extraídos são salvos, sem a imagem); considerar testar `qwen2.5-vl` para comparação, conforme decisão pendente do roadmap.
