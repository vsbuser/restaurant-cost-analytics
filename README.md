# Restaurant Cost Analytics

*[English](#english) | [Português](#português)*

---

## English

Cost management web app for restaurants: capture supplier invoices **by phone photo**, recipe cost sheets, food cost control and margin analysis.

Built as both a working product for small restaurants and a Data Analyst / Data Science portfolio project — SQL, data modeling, Python, visualization, ML engineering (local vision model) and applied machine learning in a domain I know first-hand: hospitality.

### Architecture

```
Phone (browser) ──photo──► Streamlit app ──► FastAPI + Ollama (Qwen2.5-VL) ──► structured JSON
                                │
                                └──► Supabase (PostgreSQL + Storage)
```

| Layer | Tech |
|---|---|
| UI | Streamlit (mobile browser, `st.camera_input()`) |
| Extraction | Ollama + local VLM (Claude API as pluggable fallback) |
| Backend | FastAPI |
| Database | Supabase (PostgreSQL + Storage) |
| Analysis / ML | pandas, plotly, scikit-learn, statsmodels |

### Status

🚧 Early development — see roadmap in `CONTEXTO_PROJETO.md`.

---

## Português

App web de gestão de custos para restaurantes: captura de notas fiscais de fornecedores **por foto no celular**, fichas técnicas, controle de food cost e análise de margens.

Construído com objetivo duplo: produto funcional para restaurantes pequenos e projeto de portfólio de Data Analyst / Data Science — SQL, modelagem de dados, Python, visualização, ML engineering (modelo de visão local) e machine learning aplicado a um domínio que conheço em primeira mão: hospitality.

### Status

🚧 Em desenvolvimento inicial — roadmap em `CONTEXTO_PROJETO.md`.
