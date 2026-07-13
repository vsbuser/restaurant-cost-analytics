import streamlit as st

from components.forms import editor_ingredientes
from components.theme import aplicar_tema
from services.database import (
    criar_receita,
    listar_food_cost,
    listar_ingredientes_receita,
    listar_produtos,
)

st.set_page_config(page_title="Fichas Técnicas", page_icon="📋", layout="wide")
aplicar_tema()
st.title("📋 Fichas Técnicas")

SEMAFORO_EMOJI = {"verde": "🟢", "amarelo": "🟡", "vermelho": "🔴"}
CATEGORIAS_MENU = [
    "Carnes", "Aves", "Peixes e Frutos do Mar", "Saladas",
    "Pratos Típicos", "Lanches", "Porções", "Outros",
]

produtos = listar_produtos()

tab_lista, tab_nova = st.tabs(["Fichas cadastradas", "Nova receita"])

with tab_lista:
    fichas = listar_food_cost()
    if fichas.empty:
        st.info("Nenhuma receita cadastrada ainda.")
    else:
        for _, ficha in fichas.iterrows():
            emoji = SEMAFORO_EMOJI[ficha["semaforo"]]
            titulo = (
                f"{emoji} {ficha['nome']} — food cost {ficha['food_cost_pct']}% "
                f"— custo R\\$ {ficha['custo_total']:,.2f} / venda R\\$ {ficha['preco_venda']:,.2f}"
            )
            with st.expander(titulo):
                st.caption(f"{ficha['categoria_menu']} · rende {ficha['porcoes']} porção(ões)")
                ingredientes = listar_ingredientes_receita(ficha["receita_id"])
                st.dataframe(ingredientes, hide_index=True, width="stretch")

with tab_nova:
    if produtos.empty:
        st.warning("Cadastre ao menos um produto antes de criar uma receita.")
        st.stop()

    nome = st.text_input("Nome do prato")
    col_preco, col_porcoes, col_categoria = st.columns(3)
    preco_venda = col_preco.number_input("Preço de venda (R$)", min_value=0.0, step=1.0)
    porcoes = col_porcoes.number_input("Rende quantas porções", min_value=1, step=1, value=1)
    categoria_menu = col_categoria.selectbox("Categoria do menu", CATEGORIAS_MENU)

    st.markdown("**Ingredientes**")
    ingredientes = editor_ingredientes(produtos, key_prefix="nova_receita")

    if st.button("Salvar receita", type="primary"):
        ingredientes_validos = [i for i in ingredientes if i["quantidade"] > 0]
        if not nome.strip():
            st.error("Informe o nome do prato.")
        elif preco_venda <= 0:
            st.error("Informe um preço de venda maior que zero.")
        elif not ingredientes_validos:
            st.error("Adicione ao menos um ingrediente com quantidade maior que zero.")
        else:
            ingredientes_db = [
                (int(produtos.loc[produtos["nome"] == i["produto"], "id"].iloc[0]), i["quantidade"])
                for i in ingredientes_validos
            ]
            receita_id = criar_receita(nome.strip(), preco_venda, categoria_menu, int(porcoes), ingredientes_db)
            st.session_state["nova_receita_ingredientes"] = []
            st.success(f"Receita '{nome}' (#{receita_id}) cadastrada com {len(ingredientes_db)} ingrediente(s).")
            st.rerun()
