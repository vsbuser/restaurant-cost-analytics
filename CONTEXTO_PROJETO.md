# CONTEXTO DO PROJETO — Restaurant Cost Analytics

> **Uso deste arquivo:** este arquivo vive na raiz do repositório (`CONTEXTO_PROJETO.md`). Anexe no início de cada sessão de trabalho com o Claude para retomar o contexto de onde parou. Atualize a seção "Estado atual" ao final de cada sessão.

---

## 1. Visão do projeto

Aplicação web de gestão de custos para restaurantes, inspirada no Haddock (startup de Barcelona): captura de notas fiscais de fornecedores **por foto no celular**, fichas técnicas, controle de food cost e análise de margens.

**Objetivo duplo:**
- **Produto funcional:** ferramenta real que um restaurante pequeno poderia usar pelo navegador do celular (sem app nativo — Streamlit responsivo + atalho na tela inicial).
- **Portfólio de Data Analyst / Data Scientist:** demonstrar SQL, modelagem de dados, Python, visualização, ML engineering (modelo de visão rodando localmente) e machine learning aplicado a um domínio que conheço em primeira mão (hospitality).

**Narrativa de portfólio:** "Trabalhei anos em hospitality e vivi o problema do controle de custos. Agora, como analista de dados, construí a solução." — Fio condutor do README e das entrevistas.

## 2. Arquitetura e stack

```
┌─────────────────────┐
│  Celular (browser)  │  Foto da nota via st.camera_input()
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  App Streamlit      │  UI, formulários, validação humana, dashboard
└──────┬───────┬──────┘
       │       │
┌──────▼─────┐ │ ┌────────────────────────┐
│  Supabase  │ └─►  Backend de extração    │
│  Postgres  │   │  FastAPI + Ollama (VLM) │
│  + Storage │   │  Qwen2.5-VL local       │
└────────────┘   └────────────────────────┘
```

| Camada | Tecnologia | Motivo |
|---|---|---|
| App / UI | Streamlit | Já domino; roda no navegador do celular |
| Captura da foto | `st.camera_input()` / `st.file_uploader()` | Câmera direto no browser |
| Pré-processamento | Pillow + OpenCV | Compressão, correção de perspectiva/contraste |
| Extração (IA local) | Ollama + Qwen2.5-VL (ou MiniCPM-V) | "Agente nativo": foto → JSON sem API externa |
| Backend de extração | FastAPI | Expõe o modelo local como serviço para a app |
| Camada de abstração | `extractor.py` com interface única | Trocar Ollama ↔ Claude API só por config |
| Banco de dados | Supabase (PostgreSQL + Storage) | Dados estruturados + foto original (auditoria) |
| Análise / ML | pandas, plotly, scikit-learn, statsmodels | Core do perfil DA/DS |
| Versionamento | Git + GitHub | Commits limpos, histórico apresentável |

**Decisão de arquitetura registrada:** a extração usa modelo de visão **local** (Ollama) como padrão, com a Claude API como alternativa plugável. Trade-off aceito: o Streamlit Cloud não roda o VLM, então o backend de extração roda na máquina local (ou servidor próprio) durante o desenvolvimento; a demo pública pode usar a alternativa por API.

## 3. Estrutura do repositório

```
restaurant-cost-analytics/
├── CONTEXTO_PROJETO.md        # Este arquivo (contexto para sessões com Claude)
├── README.md                  # Bilíngue EN/PT — vitrine do portfólio
├── .gitignore                 # Python, .env, __pycache__, dados locais
├── .env.example               # Modelo das variáveis (sem segredos!)
├── requirements.txt           # Dependências da app
│
├── app/                       # Aplicação Streamlit
│   ├── Home.py                # Página inicial
│   ├── pages/                 # Multipage: 1_Notas.py, 2_Fichas.py, 3_Dashboard.py
│   ├── components/            # Formulários e widgets reutilizáveis
│   └── services/
│       ├── database.py        # Conexão e queries Supabase
│       └── extractor.py       # Interface de extração (Ollama | Claude API)
│
├── backend/                   # Serviço de extração local
│   ├── main.py                # FastAPI: POST /extract (imagem → JSON)
│   ├── vision.py              # Chamada ao Ollama + prompt de extração
│   └── preprocessing.py       # OpenCV: perspectiva, contraste, resize
│
├── sql/
│   ├── schema.sql             # DDL completo do banco
│   └── views.sql              # Métricas derivadas (food cost, variações)
│
├── scripts/
│   └── generate_synthetic.py  # Gerador de dados sintéticos (12 meses)
│
├── notebooks/                 # Análises exploratórias e ML
│   ├── 01_eda.ipynb
│   └── 02_forecast.ipynb
│
├── docs/
│   ├── erd.png                # Diagrama entidade-relacionamento
│   └── decisoes.md            # Registro de decisões técnicas (ADR simplificado)
│
└── tests/                     # Testes do parser e das queries críticas
```

## 4. Etapa 0 — Setup inicial do repositório (fazer primeiro!)

Comandos para iniciar do zero com controle de versões:

```bash
# 1. Criar a estrutura de pastas
mkdir -p restaurant-cost-analytics/{app/{pages,components,services},backend,sql,scripts,notebooks,docs,tests}
cd restaurant-cost-analytics

# 2. Arquivos iniciais
touch README.md CONTEXTO_PROJETO.md requirements.txt .env.example
touch app/Home.py app/services/database.py app/services/extractor.py
touch backend/main.py backend/vision.py backend/preprocessing.py
touch sql/schema.sql sql/views.sql scripts/generate_synthetic.py

# 3. .gitignore (essencial ANTES do primeiro commit)
cat > .gitignore << 'EOF'
.env
__pycache__/
*.pyc
.venv/
venv/
.ipynb_checkpoints/
*.db
data/local/
.DS_Store
EOF

# 4. Ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 5. Git local
git init
git add .
git commit -m "chore: initial project structure"

# 6. Conectar ao GitHub (criar o repo vazio em github.com antes)
git remote add origin https://github.com/SEU_USUARIO/restaurant-cost-analytics.git
git branch -M main
git push -u origin main
```

**Regras de ouro do versionamento:**
- `.env` com credenciais do Supabase **nunca** entra no Git — só o `.env.example` com nomes das variáveis
- Commits pequenos e frequentes, em inglês: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`
- Uma branch por etapa do roadmap (`etapa-1-schema`, `etapa-2-dados`...), merge na `main` ao concluir — o histórico de PRs vira evidência de método de trabalho para recrutadores

✅ Critério de conclusão: repositório no GitHub com estrutura completa, `.gitignore` correto e primeiro commit feito.

## 5. Modelo de dados preliminar

Entidades principais (schema `restaurant`):

- **fornecedores** (id, nome, categoria, contato)
- **produtos** (id, nome, unidade_medida, categoria) — insumos/ingredientes
- **notas_fiscais** (id, fornecedor_id, data, total, fonte: `foto_ia` / `manual` / `csv`, foto_url)
- **nota_linhas** (id, nota_id, produto_id, quantidade, preco_unitario)
- **receitas** (id, nome, preco_venda, categoria_menu, porcoes)
- **receita_ingredientes** (id, receita_id, produto_id, quantidade)
- **vendas** (id, receita_id, data, unidades) — para análise de demanda

**Métricas derivadas (views SQL):** preço médio ponderado por produto/mês; custo dinâmico de cada receita (último preço); food cost % por prato; variação de preço por fornecedor com alerta se subir > X%.

## 6. Roadmap em 7 etapas

### Etapa 1 — Modelo de dados e fundamentos
- DDL completo em `sql/schema.sql` + criação no Supabase
- ERD no dbdiagram.io → exportar para `docs/erd.png`
- **Aprendizado:** normalização, chaves estrangeiras, design de schemas
- ✅ Schema criado, versionado e documentado

### Etapa 2 — Gerador de dados sintéticos
- `scripts/generate_synthetic.py`: 12 meses de notas realistas com sazonalidade, inflação gradual e variação entre fornecedores
- **Aprendizado:** simulação de dados, distribuições, carga em lote
- ✅ Banco populado com dados coerentes e verificáveis

### Etapa 3 — App base: CRUD de notas fiscais
- Streamlit multipage conectado ao Supabase: registro manual e por CSV
- Listagem e edição de fornecedores e produtos
- **Aprendizado:** arquitetura da app, formulários, validação
- ✅ Registrar uma nota completa pela app (inclusive pelo celular)

### Etapa 4 — Fichas técnicas e food cost
- Receitas com ingredientes e custo dinâmico
- Food cost % com semáforo (verde < 30%, amarelo 30–35%, vermelho > 35%)
- **Aprendizado:** SQL avançado (joins, window functions, views)
- ✅ Ficha técnica de 10 pratos com custos atualizados em tempo real

### Etapa 5 — Dashboard analítico
- KPIs: food cost global, evolução de preços, top insumos que mais sobem, comparativo de fornecedores, alertas de variação
- **Aprendizado:** visualização, storytelling com dados, design de KPIs
- ✅ Dashboard navegável com pelo menos 5 gráficos com insight real

### Etapa 6 — Extração de notas por foto com IA local
- `st.camera_input()` no celular → pré-processamento (OpenCV) → backend FastAPI → Ollama (Qwen2.5-VL) → JSON estruturado → tela de validação humana → inserção no banco + foto no Supabase Storage
- Camada `extractor.py` com interface única, permitindo trocar Ollama ↔ Claude API por configuração
- **Aprendizado:** VLMs locais, prompt engineering para structured output, design de abstrações, FastAPI
- ✅ Uma foto real de nota processada de ponta a ponta pelo celular

### Etapa 7 — Módulo preditivo + fechamento do portfólio
- Forecast de preço de insumos-chave (3 meses) e/ou previsão de demanda por prato
- README final bilíngue com capturas, ERD, arquitetura e decisões técnicas; demo pública (Streamlit Cloud com extração via API como fallback)
- Post no LinkedIn contando a história hospitality → data
- **Aprendizado:** séries temporais, avaliação de modelos, comunicação
- ✅ Demo pública + repositório apresentável a recrutadores

## 7. Convenções de trabalho

- **Repositório:** `restaurant-cost-analytics`
- **Idioma:** código, commits e README em inglês; este arquivo de contexto e nossa comunicação em português brasileiro
- **Método didático:** em cada etapa, o Claude explica os conceitos antes de entregar código; o objetivo é aprender, não apenas copiar
- **Registro de decisões:** toda decisão técnica relevante vai para `docs/decisoes.md` (o que, por quê, alternativas descartadas)

## 8. Estado atual

- **Etapa atual:** 0 — Setup do repositório (não iniciada)
- **Última sessão:** 09/07/2026 — definição da arquitetura com extração local (Ollama) e estrutura do repositório
- **Próximo passo:** executar a Etapa 0 (criar estrutura, git init, primeiro push no GitHub)
- **Decisões tomadas:** extração por foto com VLM local via Ollama como padrão, Claude API como alternativa plugável; app mobile via navegador (sem app nativo); MVP para um único estabelecimento
- **Decisões pendentes:** nome definitivo da app; modelo VLM final (Qwen2.5-VL vs MiniCPM-V — testar os dois na Etapa 6)
