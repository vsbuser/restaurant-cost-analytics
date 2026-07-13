import streamlit as st

from components.theme import aplicar_tema, kpi_card
from services.database import listar_fornecedores, listar_notas, listar_produtos

st.set_page_config(page_title="RestaurApp", page_icon="🍽️", layout="wide")
aplicar_tema()

st.markdown(
    '<div style="font-family:\'Poppins\',sans-serif;font-weight:700;font-size:30px;'
    'color:#16211a;margin-bottom:2px;">🍽️ RestaurApp</div>',
    unsafe_allow_html=True,
)
st.caption("Controle de custos, fichas técnicas e food cost para restaurantes.")

fornecedores = listar_fornecedores()
produtos = listar_produtos()
notas = listar_notas(limite=1000)

col1, col2, col3 = st.columns(3)
with col1:
    kpi_card("Fornecedores", len(fornecedores))
with col2:
    kpi_card("Produtos cadastrados", len(produtos))
with col3:
    kpi_card("Notas registradas", len(notas))

st.divider()
st.markdown(
    "Use o menu à esquerda para cadastrar **fornecedores**, **produtos**, registrar **notas fiscais**, "
    "montar **fichas técnicas** e acompanhar o **dashboard** analítico."
)
