import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.theme import INK_MUTED, STATUS_CRITICAL, STATUS_GOOD, STATUS_WARNING, aplicar_tema, kpi_card
from services.database import (
    food_cost_global,
    listar_food_cost,
    listar_gasto_por_fornecedor,
    listar_preco_medio_mensal,
    listar_receita_por_categoria,
    listar_top_produtos_por_gasto,
    listar_variacao_precos,
)

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
aplicar_tema()
st.title("📊 Dashboard Analítico")

STATUS = {"verde": STATUS_GOOD, "amarelo": STATUS_WARNING, "vermelho": STATUS_CRITICAL}
CATEGORICAL = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]
MUTED = INK_MUTED
CRITICAL = STATUS_CRITICAL
SEQ_GREEN = ["#d8f0e4", "#b7e3cd", "#8ed3b0", "#57bd8d", "#1e8f5e", "#146b47", "#0d4f34"]

CHART_LAYOUT = dict(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font_color="#16211a",
    margin=dict(t=30, l=10, r=10, b=10),
)
GRID = dict(gridcolor="#e1e8dc", zerolinecolor="#c3c2b7")

fichas = listar_food_cost()
variacoes = listar_variacao_precos()
gasto_fornecedor = listar_gasto_por_fornecedor()
receita_categoria = listar_receita_por_categoria()
top_produtos = listar_top_produtos_por_gasto(5)

# ---------------------------------------------------------------
# KPIs
# ---------------------------------------------------------------
def fmt_moeda(valor):
    if valor >= 1_000_000:
        return f"R$ {valor / 1_000_000:.2f}M"
    if valor >= 1_000:
        return f"R$ {valor / 1_000:.1f}K"
    return f"R$ {valor:,.2f}"


col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Food cost global", f"{food_cost_global()}%", accent=STATUS_GOOD)
with col2:
    kpi_card("Gasto total em compras", fmt_moeda(gasto_fornecedor["gasto_total"].sum()))
with col3:
    kpi_card("Receita total (vendas)", fmt_moeda(receita_categoria["receita_total"].sum()))
with col4:
    n_alertas = int(variacoes["alerta"].sum())
    kpi_card("Alertas de variação de preço", n_alertas, accent=STATUS_CRITICAL if n_alertas else STATUS_GOOD)

st.divider()

# ---------------------------------------------------------------
# 1. Food cost % por prato — cor de status (estado, não ranking)
# ---------------------------------------------------------------
st.subheader("Food cost % por prato")
fig1 = go.Figure(go.Bar(
    x=fichas["food_cost_pct"],
    y=fichas["nome"],
    orientation="h",
    marker_color=[STATUS[s] for s in fichas["semaforo"]],
    hovertemplate="%{y}: %{x}%<extra></extra>",
))
fig1.update_layout(**CHART_LAYOUT, xaxis=dict(title="Food cost %", **GRID), yaxis=dict(autorange="reversed"), height=380)
st.plotly_chart(fig1, width="stretch")

# ---------------------------------------------------------------
# 2. Evolução do preço médio mensal dos insumos-chave — categórica
# ---------------------------------------------------------------
st.subheader("Evolução do preço médio mensal — top 5 insumos por gasto")
precos_mensais = listar_preco_medio_mensal(top_produtos["produto"])
fig2 = go.Figure()
for i, produto in enumerate(top_produtos["produto"]):
    serie = precos_mensais[precos_mensais["produto"] == produto]
    fig2.add_trace(go.Scatter(
        x=serie["mes"], y=serie["preco_medio_ponderado"], name=produto,
        mode="lines+markers", line=dict(color=CATEGORICAL[i % len(CATEGORICAL)], width=2),
        marker=dict(size=6),
        hovertemplate=f"{produto}: R$ %{{y:.2f}}<extra></extra>",
    ))
fig2.update_layout(**CHART_LAYOUT, xaxis=dict(title="Mês", **GRID), yaxis=dict(title="Preço médio ponderado (R$)", **GRID), height=380)
st.plotly_chart(fig2, width="stretch")

# ---------------------------------------------------------------
# 3. Top insumos que mais sobem — emphasis (alerta em destaque, resto neutro)
# ---------------------------------------------------------------
st.subheader("Variação de preço por insumo (última compra vs. anterior)")
top_variacao = variacoes.head(10)
fig3 = go.Figure(go.Bar(
    x=top_variacao["variacao_pct"],
    y=top_variacao["produto"],
    orientation="h",
    marker_color=[CRITICAL if a else MUTED for a in top_variacao["alerta"]],
    hovertemplate="%{y}: %{x}%<extra></extra>",
))
fig3.add_vline(x=10, line_dash="dash", line_color=CRITICAL, annotation_text="limite de alerta (10%)")
fig3.update_layout(**CHART_LAYOUT, xaxis=dict(title="Variação %", **GRID), yaxis=dict(autorange="reversed"), height=380)
st.plotly_chart(fig3, width="stretch")

if variacoes["alerta"].any():
    st.caption("Insumos com alerta ativo (subiram mais de 10% na última compra):")
    st.dataframe(
        variacoes[variacoes["alerta"]][["produto", "fornecedor", "preco_anterior", "preco_atual", "variacao_pct"]],
        hide_index=True, width="stretch",
    )

col_a, col_b = st.columns(2)

# ---------------------------------------------------------------
# 4. Comparativo de fornecedores por gasto total — sequencial (magnitude)
# ---------------------------------------------------------------
with col_a:
    st.subheader("Gasto total por fornecedor")
    fig4 = px.bar(
        gasto_fornecedor, x="gasto_total", y="fornecedor", orientation="h",
        color="gasto_total", color_continuous_scale=SEQ_GREEN,
    )
    fig4.update_traces(hovertemplate="%{y}: R$ %{x:,.2f}<extra></extra>")
    fig4.update_layout(**CHART_LAYOUT, xaxis=dict(title="Gasto total (R$)", **GRID),
                        yaxis=dict(title="", autorange="reversed"), coloraxis_showscale=False, height=340)
    st.plotly_chart(fig4, width="stretch")

# ---------------------------------------------------------------
# 5. Receita por categoria de menu — sequencial (magnitude)
# ---------------------------------------------------------------
with col_b:
    st.subheader("Receita por categoria de menu")
    fig5 = px.bar(
        receita_categoria, x="receita_total", y="categoria_menu", orientation="h",
        color="receita_total", color_continuous_scale=SEQ_GREEN,
    )
    fig5.update_traces(hovertemplate="%{y}: R$ %{x:,.2f}<extra></extra>")
    fig5.update_layout(**CHART_LAYOUT, xaxis=dict(title="Receita (R$)", **GRID),
                        yaxis=dict(title="", autorange="reversed"), coloraxis_showscale=False, height=340)
    st.plotly_chart(fig5, width="stretch")
