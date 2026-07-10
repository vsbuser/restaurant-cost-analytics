import streamlit as st

from services.database import listar_fornecedores, listar_notas, listar_produtos

st.set_page_config(page_title="Restaurant Cost Analytics", page_icon="🍽️", layout="wide")

st.title("🍽️ Restaurant Cost Analytics")
st.caption("Controle de custos, fichas técnicas e food cost para restaurantes.")

fornecedores = listar_fornecedores()
produtos = listar_produtos()
notas = listar_notas(limite=1000)

col1, col2, col3 = st.columns(3)
col1.metric("Fornecedores", len(fornecedores))
col2.metric("Produtos cadastrados", len(produtos))
col3.metric("Notas registradas", len(notas))

st.divider()
st.markdown(
    "Use o menu à esquerda para cadastrar **fornecedores**, **produtos** e registrar **notas fiscais**."
)
