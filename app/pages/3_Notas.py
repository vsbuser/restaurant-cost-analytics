from datetime import date

import pandas as pd
import streamlit as st

from components.forms import editor_linhas_nota
from components.theme import aplicar_tema
from services.database import (
    criar_nota_fiscal,
    listar_fornecedores,
    listar_linhas_da_nota,
    listar_notas,
    listar_produtos,
)

st.set_page_config(page_title="Notas Fiscais", page_icon="🧾", layout="wide")
aplicar_tema()
st.title("🧾 Notas Fiscais")

fornecedores = listar_fornecedores()
produtos = listar_produtos()

if fornecedores.empty or produtos.empty:
    st.warning("Cadastre ao menos um fornecedor e um produto antes de registrar uma nota.")
    st.stop()

tab_nova, tab_csv, tab_listagem = st.tabs(["Nova nota", "Importar CSV", "Notas registradas"])

with tab_nova:
    fornecedor_nome = st.selectbox("Fornecedor", fornecedores["nome"], key="fornecedor_manual")
    data_compra = st.date_input("Data da compra", value=date.today(), max_value=date.today(), key="data_manual")

    st.markdown("**Itens da nota**")
    linhas = editor_linhas_nota(produtos, key_prefix="manual")

    total = sum(linha["quantidade"] * linha["preco"] for linha in linhas)
    st.metric("Total da nota", f"R$ {total:,.2f}")

    if st.button("Salvar nota", type="primary"):
        linhas_validas = [linha for linha in linhas if linha["quantidade"] > 0]
        if not linhas_validas:
            st.error("Adicione ao menos um item com quantidade maior que zero.")
        else:
            fornecedor_id = int(fornecedores.loc[fornecedores["nome"] == fornecedor_nome, "id"].iloc[0])
            linhas_db = [
                (int(produtos.loc[produtos["nome"] == linha["produto"], "id"].iloc[0]),
                 linha["quantidade"], linha["preco"])
                for linha in linhas_validas
            ]
            nota_id = criar_nota_fiscal(fornecedor_id, data_compra, "manual", linhas_db)
            st.session_state["manual_linhas"] = []
            st.success(f"Nota #{nota_id} registrada com {len(linhas_db)} item(ns).")
            st.rerun()

with tab_csv:
    st.caption("CSV com colunas: produto, quantidade, preco_unitario — uma linha por item da nota.")
    fornecedor_nome_csv = st.selectbox("Fornecedor", fornecedores["nome"], key="fornecedor_csv")
    data_csv = st.date_input("Data da compra", value=date.today(), max_value=date.today(), key="data_csv")
    arquivo = st.file_uploader("Arquivo CSV", type="csv")

    if arquivo is not None:
        df_csv = pd.read_csv(arquivo)
        faltantes = {"produto", "quantidade", "preco_unitario"} - set(df_csv.columns)
        if faltantes:
            st.error(f"Colunas faltando no CSV: {', '.join(faltantes)}")
        else:
            df_csv = df_csv.merge(produtos[["id", "nome"]], left_on="produto", right_on="nome", how="left")
            nao_encontrados = df_csv[df_csv["id"].isna()]["produto"].unique()
            if len(nao_encontrados):
                st.error(f"Produto(s) não cadastrado(s): {', '.join(nao_encontrados)}")
            else:
                st.dataframe(df_csv[["produto", "quantidade", "preco_unitario"]], hide_index=True)
                total_csv = (df_csv["quantidade"] * df_csv["preco_unitario"]).sum()
                st.metric("Total da nota", f"R$ {total_csv:,.2f}")
                if st.button("Confirmar importação"):
                    fornecedor_id = int(
                        fornecedores.loc[fornecedores["nome"] == fornecedor_nome_csv, "id"].iloc[0]
                    )
                    linhas_db = [
                        (int(linha["id"]), float(linha["quantidade"]), float(linha["preco_unitario"]))
                        for _, linha in df_csv.iterrows()
                    ]
                    nota_id = criar_nota_fiscal(fornecedor_id, data_csv, "csv", linhas_db)
                    st.success(f"Nota #{nota_id} importada com {len(linhas_db)} item(ns).")

with tab_listagem:
    notas = listar_notas()
    if notas.empty:
        st.info("Nenhuma nota registrada ainda.")
    else:
        for _, nota in notas.iterrows():
            titulo = f"#{nota['id']} — {nota['fornecedor']} — {nota['data']} — R$ {nota['total']:,.2f}"
            with st.expander(titulo):
                linhas_nota = listar_linhas_da_nota(nota["id"])
                st.dataframe(linhas_nota, hide_index=True, width="stretch")
