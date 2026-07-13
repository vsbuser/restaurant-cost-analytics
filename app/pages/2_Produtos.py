import streamlit as st

from components.theme import aplicar_tema
from services.database import UNIDADES_MEDIDA, atualizar_produto, criar_produto, listar_produtos

st.set_page_config(page_title="Produtos", page_icon="🥔", layout="wide")
aplicar_tema()
st.title("🥔 Produtos")

CATEGORIAS = ["hortifruti", "carnes", "peixes", "bebidas", "laticinios", "limpeza", "outros"]

produtos = listar_produtos()

st.subheader("Cadastrados")
editado = st.data_editor(
    produtos,
    column_config={
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "unidade_medida": st.column_config.SelectboxColumn("Unidade", options=UNIDADES_MEDIDA),
        "categoria": st.column_config.SelectboxColumn("Categoria", options=CATEGORIAS),
    },
    hide_index=True,
    width="stretch",
    key="editor_produtos",
)

if st.button("Salvar alterações", key="salvar_produtos"):
    comparacao = editado.merge(produtos, on="id", suffixes=("_novo", "_antigo"))
    alterados = comparacao[
        (comparacao["nome_novo"] != comparacao["nome_antigo"])
        | (comparacao["unidade_medida_novo"] != comparacao["unidade_medida_antigo"])
        | (comparacao["categoria_novo"] != comparacao["categoria_antigo"])
    ]
    for _, linha in alterados.iterrows():
        atualizar_produto(
            linha["id"], linha["nome_novo"], linha["unidade_medida_novo"], linha["categoria_novo"]
        )
    if len(alterados):
        st.success(f"{len(alterados)} produto(s) atualizado(s).")
        st.rerun()
    else:
        st.info("Nenhuma alteração para salvar.")

st.divider()
st.subheader("Novo produto")
with st.form("novo_produto", clear_on_submit=True):
    nome = st.text_input("Nome")
    unidade = st.selectbox("Unidade de medida", UNIDADES_MEDIDA)
    categoria = st.selectbox("Categoria", CATEGORIAS)
    if st.form_submit_button("Cadastrar"):
        if not nome.strip():
            st.error("Informe o nome do produto.")
        else:
            criar_produto(nome.strip(), unidade, categoria)
            st.success(f"Produto '{nome}' cadastrado.")
            st.rerun()
