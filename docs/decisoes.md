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
