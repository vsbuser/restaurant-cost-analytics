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
from services.extractor import extrair_nota

st.set_page_config(page_title="Notas Fiscais", page_icon="🧾", layout="wide")
aplicar_tema()
st.title("🧾 Notas Fiscais")

fornecedores = listar_fornecedores()
produtos = listar_produtos()

if fornecedores.empty or produtos.empty:
    st.warning("Cadastre ao menos um fornecedor e um produto antes de registrar uma nota.")
    st.stop()

tab_nova, tab_foto, tab_csv, tab_listagem = st.tabs(
    ["Nova nota", "Tirar foto", "Importar CSV", "Notas registradas"]
)

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

with tab_foto:
    st.caption(
        "Tire uma foto da nota fiscal pelo celular (ou envie uma imagem). "
        "A IA extrai os itens automaticamente — revise antes de salvar."
    )
    foto = st.camera_input("Foto da nota", key="foto_camera")
    if foto is None:
        foto = st.file_uploader("Ou envie uma imagem da nota", type=["jpg", "jpeg", "png"], key="foto_upload")

    if foto is not None and st.session_state.get("foto_bytes_processado") != foto.getvalue():
        with st.spinner("Extraindo dados da nota..."):
            try:
                st.session_state["foto_dados_extraidos"] = extrair_nota(foto.getvalue())
                st.session_state["foto_bytes_processado"] = foto.getvalue()
            except Exception as exc:
                st.error(f"Não foi possível extrair os dados: {exc}")
                st.session_state.pop("foto_dados_extraidos", None)

    dados_foto = st.session_state.get("foto_dados_extraidos")
    if dados_foto:
        st.success("Dados extraídos — confira e ajuste antes de salvar.")

        fornecedor_nomes = list(fornecedores["nome"])
        sugestao_fornecedor = dados_foto.get("fornecedor")
        indice_fornecedor = (
            fornecedor_nomes.index(sugestao_fornecedor) if sugestao_fornecedor in fornecedor_nomes else 0
        )
        fornecedor_nome_foto = st.selectbox(
            "Fornecedor", fornecedor_nomes, index=indice_fornecedor, key="fornecedor_foto"
        )

        data_sugerida = date.today()
        if dados_foto.get("data"):
            try:
                data_sugerida = date.fromisoformat(dados_foto["data"])
            except ValueError:
                pass
        data_foto = st.date_input(
            "Data da compra", value=data_sugerida, max_value=date.today(), key="data_foto"
        )

        st.markdown("**Itens extraídos (edite se necessário)**")
        produtos_nomes = list(produtos["nome"])
        itens_editaveis = []
        for i, item in enumerate(dados_foto.get("itens") or []):
            col1, col2, col3 = st.columns([3, 2, 2])
            nome_sugerido = item.get("produto", "")
            indice_produto = produtos_nomes.index(nome_sugerido) if nome_sugerido in produtos_nomes else 0
            produto_sel = col1.selectbox(
                "Produto", produtos_nomes, index=indice_produto, key=f"foto_produto_{i}"
            )
            qtd_sel = col2.number_input(
                "Quantidade", min_value=0.0, step=0.1,
                value=float(item.get("quantidade") or 0), key=f"foto_qtd_{i}",
            )
            preco_sel = col3.number_input(
                "Preço unitário", min_value=0.0, step=0.1,
                value=float(item.get("preco_unitario") or 0), key=f"foto_preco_{i}",
            )
            itens_editaveis.append((produto_sel, qtd_sel, preco_sel))

        total_foto = sum(qtd * preco for _, qtd, preco in itens_editaveis)
        st.metric("Total da nota", f"R$ {total_foto:,.2f}")

        if st.button("Confirmar e salvar", type="primary", key="salvar_foto"):
            itens_validos = [(p, q, pr) for p, q, pr in itens_editaveis if q > 0]
            if not itens_validos:
                st.error("Nenhum item com quantidade válida.")
            else:
                fornecedor_id = int(
                    fornecedores.loc[fornecedores["nome"] == fornecedor_nome_foto, "id"].iloc[0]
                )
                linhas_db = [
                    (int(produtos.loc[produtos["nome"] == p, "id"].iloc[0]), q, pr)
                    for p, q, pr in itens_validos
                ]
                nota_id = criar_nota_fiscal(fornecedor_id, data_foto, "foto_ia", linhas_db)
                for chave in ["foto_dados_extraidos", "foto_bytes_processado"]:
                    st.session_state.pop(chave, None)
                st.success(f"Nota #{nota_id} registrada a partir da foto com {len(linhas_db)} item(ns).")
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
