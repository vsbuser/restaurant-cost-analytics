import os
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
import psycopg2
import streamlit as st
from psycopg2 import pool
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

UNIDADES_MEDIDA = ["kg", "g", "L", "ml", "un", "cx", "dz"]
FONTES_NOTA = ["manual", "csv", "foto_ia"]


@st.cache_resource
def get_pool():
    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        st.error("SUPABASE_DB_URL não configurado no .env")
        st.stop()
    return pool.ThreadedConnectionPool(1, 5, db_url)


@contextmanager
def get_connection():
    conn_pool = get_pool()
    conn = conn_pool.getconn()

    # o pooler do Supabase encerra conexões ociosas; um "ping" barato evita
    # devolver ao chamador uma conexão que já morreu do lado do servidor.
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
    except psycopg2.OperationalError:
        conn_pool.putconn(conn, close=True)
        conn = conn_pool.getconn()

    saudavel = True
    try:
        yield conn
    except psycopg2.OperationalError:
        saudavel = False
        raise
    finally:
        conn_pool.putconn(conn, close=not saudavel)


def _query_df(sql, params=None):
    with get_connection() as conn:
        return pd.read_sql(sql, conn, params=params)


def listar_fornecedores():
    return _query_df("SELECT id, nome, categoria, contato FROM restaurant.fornecedores ORDER BY nome")


def criar_fornecedor(nome, categoria, contato):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO restaurant.fornecedores (nome, categoria, contato) "
                "VALUES (%s, %s, %s) RETURNING id",
                (nome, categoria, contato),
            )
            novo_id = cur.fetchone()[0]
        conn.commit()
    return novo_id


def atualizar_fornecedor(id_, nome, categoria, contato):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE restaurant.fornecedores SET nome=%s, categoria=%s, contato=%s WHERE id=%s",
                (nome, categoria, contato, id_),
            )
        conn.commit()


def listar_produtos():
    return _query_df("SELECT id, nome, unidade_medida, categoria FROM restaurant.produtos ORDER BY nome")


def criar_produto(nome, unidade_medida, categoria):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO restaurant.produtos (nome, unidade_medida, categoria) "
                "VALUES (%s, %s, %s) RETURNING id",
                (nome, unidade_medida, categoria),
            )
            novo_id = cur.fetchone()[0]
        conn.commit()
    return novo_id


def atualizar_produto(id_, nome, unidade_medida, categoria):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE restaurant.produtos SET nome=%s, unidade_medida=%s, categoria=%s WHERE id=%s",
                (nome, unidade_medida, categoria, id_),
            )
        conn.commit()


def listar_notas(limite=100):
    return _query_df(
        """
        SELECT nf.id, nf.data, f.nome AS fornecedor, nf.total, nf.fonte
        FROM restaurant.notas_fiscais nf
        JOIN restaurant.fornecedores f ON f.id = nf.fornecedor_id
        ORDER BY nf.data DESC, nf.id DESC
        LIMIT %s
        """,
        params=(limite,),
    )


def listar_linhas_da_nota(nota_id):
    return _query_df(
        """
        SELECT p.nome AS produto, nl.quantidade, p.unidade_medida, nl.preco_unitario,
               (nl.quantidade * nl.preco_unitario) AS subtotal
        FROM restaurant.nota_linhas nl
        JOIN restaurant.produtos p ON p.id = nl.produto_id
        WHERE nl.nota_id = %s
        ORDER BY p.nome
        """,
        params=(nota_id,),
    )


def listar_food_cost():
    return _query_df(
        "SELECT receita_id, nome, categoria_menu, porcoes, preco_venda, custo_total, "
        "food_cost_pct, semaforo FROM restaurant.vw_food_cost ORDER BY food_cost_pct DESC"
    )


def listar_ingredientes_receita(receita_id):
    return _query_df(
        """
        SELECT p.nome AS produto, ri.quantidade, p.unidade_medida,
               up.ultimo_preco, (ri.quantidade * up.ultimo_preco) AS subtotal
        FROM restaurant.receita_ingredientes ri
        JOIN restaurant.produtos p ON p.id = ri.produto_id
        LEFT JOIN restaurant.vw_ultimo_preco_produto up ON up.produto_id = ri.produto_id
        WHERE ri.receita_id = %s
        ORDER BY p.nome
        """,
        params=(receita_id,),
    )


def criar_receita(nome, preco_venda, categoria_menu, porcoes, ingredientes):
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO restaurant.receitas (nome, preco_venda, categoria_menu, porcoes) "
                    "VALUES (%s, %s, %s, %s) RETURNING id",
                    (nome, preco_venda, categoria_menu, porcoes),
                )
                receita_id = cur.fetchone()[0]
                for produto_id, quantidade in ingredientes:
                    cur.execute(
                        "INSERT INTO restaurant.receita_ingredientes (receita_id, produto_id, quantidade) "
                        "VALUES (%s, %s, %s)",
                        (receita_id, produto_id, quantidade),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return receita_id


def criar_nota_fiscal(fornecedor_id, data, fonte, linhas):
    total = round(sum(qtd * preco for _, qtd, preco in linhas), 2)
    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO restaurant.notas_fiscais (fornecedor_id, data, total, fonte) "
                    "VALUES (%s, %s, %s, %s) RETURNING id",
                    (fornecedor_id, data, total, fonte),
                )
                nota_id = cur.fetchone()[0]
                for produto_id, quantidade, preco_unitario in linhas:
                    cur.execute(
                        "INSERT INTO restaurant.nota_linhas "
                        "(nota_id, produto_id, quantidade, preco_unitario) VALUES (%s, %s, %s, %s)",
                        (nota_id, produto_id, quantidade, preco_unitario),
                    )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return nota_id
