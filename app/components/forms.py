import streamlit as st


def editor_linhas_nota(produtos_df, key_prefix):
    state_key = f"{key_prefix}_linhas"
    if state_key not in st.session_state:
        st.session_state[state_key] = []

    linhas = st.session_state[state_key]
    nomes_produtos = list(produtos_df["nome"])

    for i, linha in enumerate(linhas):
        col_produto, col_qtd, col_preco, col_remover = st.columns([3, 2, 2, 1])

        indice_atual = nomes_produtos.index(linha["produto"]) if linha["produto"] in nomes_produtos else 0
        linha["produto"] = col_produto.selectbox(
            "Produto", nomes_produtos, index=indice_atual, key=f"{key_prefix}_produto_{i}",
        )
        linha["quantidade"] = col_qtd.number_input(
            "Quantidade", min_value=0.0, step=0.5, value=linha["quantidade"], key=f"{key_prefix}_qtd_{i}",
        )
        linha["preco"] = col_preco.number_input(
            "Preço unitário", min_value=0.0, step=0.1, value=linha["preco"], key=f"{key_prefix}_preco_{i}",
        )
        col_remover.markdown("&nbsp;")
        if col_remover.button("🗑", key=f"{key_prefix}_remover_{i}"):
            linhas.pop(i)
            st.rerun()

    if st.button("+ Adicionar item", key=f"{key_prefix}_add"):
        linhas.append({"produto": nomes_produtos[0], "quantidade": 1.0, "preco": 0.0})
        st.rerun()

    return linhas


def editor_ingredientes(produtos_df, key_prefix):
    state_key = f"{key_prefix}_ingredientes"
    if state_key not in st.session_state:
        st.session_state[state_key] = []

    ingredientes = st.session_state[state_key]
    nomes_produtos = list(produtos_df["nome"])

    for i, item in enumerate(ingredientes):
        col_produto, col_qtd, col_remover = st.columns([3, 2, 1])

        indice_atual = nomes_produtos.index(item["produto"]) if item["produto"] in nomes_produtos else 0
        item["produto"] = col_produto.selectbox(
            "Produto", nomes_produtos, index=indice_atual, key=f"{key_prefix}_produto_{i}",
        )
        item["quantidade"] = col_qtd.number_input(
            "Quantidade", min_value=0.0, step=0.05, value=item["quantidade"], key=f"{key_prefix}_qtd_{i}",
        )
        col_remover.markdown("&nbsp;")
        if col_remover.button("🗑", key=f"{key_prefix}_remover_{i}"):
            ingredientes.pop(i)
            st.rerun()

    if st.button("+ Adicionar ingrediente", key=f"{key_prefix}_add"):
        ingredientes.append({"produto": nomes_produtos[0], "quantidade": 0.1})
        st.rerun()

    return ingredientes
