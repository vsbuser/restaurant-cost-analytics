import streamlit as st

from services.database import atualizar_fornecedor, criar_fornecedor, listar_fornecedores

st.set_page_config(page_title="Fornecedores", page_icon="🚚")
st.title("Fornecedores")

CATEGORIAS = ["hortifruti", "carnes", "peixes", "bebidas", "laticinios", "limpeza", "outros"]

fornecedores = listar_fornecedores()

st.subheader("Cadastrados")
editado = st.data_editor(
    fornecedores,
    column_config={
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "categoria": st.column_config.SelectboxColumn("Categoria", options=CATEGORIAS),
    },
    hide_index=True,
    width="stretch",
    key="editor_fornecedores",
)

if st.button("Salvar alterações"):
    comparacao = editado.merge(fornecedores, on="id", suffixes=("_novo", "_antigo"))
    alterados = comparacao[
        (comparacao["nome_novo"] != comparacao["nome_antigo"])
        | (comparacao["categoria_novo"] != comparacao["categoria_antigo"])
        | (comparacao["contato_novo"] != comparacao["contato_antigo"])
    ]
    for _, linha in alterados.iterrows():
        atualizar_fornecedor(linha["id"], linha["nome_novo"], linha["categoria_novo"], linha["contato_novo"])
    if len(alterados):
        st.success(f"{len(alterados)} fornecedor(es) atualizado(s).")
        st.rerun()
    else:
        st.info("Nenhuma alteração para salvar.")

st.divider()
st.subheader("Novo fornecedor")
with st.form("novo_fornecedor", clear_on_submit=True):
    nome = st.text_input("Nome")
    categoria = st.selectbox("Categoria", CATEGORIAS)
    contato = st.text_input("Contato (telefone/e-mail)")
    if st.form_submit_button("Cadastrar"):
        if not nome.strip():
            st.error("Informe o nome do fornecedor.")
        else:
            criar_fornecedor(nome.strip(), categoria, contato.strip() or None)
            st.success(f"Fornecedor '{nome}' cadastrado.")
            st.rerun()
