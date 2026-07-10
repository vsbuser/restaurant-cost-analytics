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
