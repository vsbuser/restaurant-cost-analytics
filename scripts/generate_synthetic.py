import argparse
import math
import os
import random
from datetime import date, timedelta

import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

FORNECEDORES = [
    {"nome": "Hortifruti Bom Preço", "categoria": "hortifruti", "contato": "(11) 91234-0001"},
    {"nome": "Frigorífico Boi Manso", "categoria": "carnes", "contato": "(11) 91234-0002"},
    {"nome": "Peixaria Maré Alta", "categoria": "peixes", "contato": "(11) 91234-0003"},
    {"nome": "Distribuidora Bebidas Litoral", "categoria": "bebidas", "contato": "(11) 91234-0004"},
    {"nome": "Empório Laticínios Serra Azul", "categoria": "laticinios", "contato": "(11) 91234-0005"},
    {"nome": "Higiene Total Descartáveis", "categoria": "limpeza", "contato": "(11) 91234-0006"},
]

# (nome, unidade_medida, categoria_fornecedor, preco_base, faixa_quantidade_por_compra)
PRODUTOS = [
    ("Tomate", "kg", "hortifruti", 5.50, (10, 40)),
    ("Cebola", "kg", "hortifruti", 4.20, (8, 30)),
    ("Alface", "un", "hortifruti", 2.80, (20, 60)),
    ("Batata", "kg", "hortifruti", 4.80, (15, 50)),
    ("Limão", "kg", "hortifruti", 6.00, (5, 20)),
    ("Picanha", "kg", "carnes", 62.00, (10, 30)),
    ("Peito de frango", "kg", "carnes", 14.50, (15, 40)),
    ("Linguiça", "kg", "carnes", 18.00, (8, 25)),
    ("Costela bovina", "kg", "carnes", 28.00, (10, 25)),
    ("Camarão", "kg", "peixes", 55.00, (5, 15)),
    ("Filé de tilápia", "kg", "peixes", 32.00, (8, 20)),
    ("Refrigerante lata", "un", "bebidas", 3.20, (48, 144)),
    ("Cerveja long neck", "un", "bebidas", 4.50, (48, 144)),
    ("Água mineral", "L", "bebidas", 2.00, (24, 96)),
    ("Queijo mussarela", "kg", "laticinios", 32.00, (5, 20)),
    ("Leite", "L", "laticinios", 4.80, (10, 40)),
    ("Farinha de trigo", "kg", "laticinios", 5.20, (10, 30)),
    ("Arroz", "kg", "laticinios", 6.00, (20, 60)),
    ("Feijão", "kg", "laticinios", 8.50, (15, 40)),
    ("Azeite de oliva", "L", "laticinios", 28.00, (3, 10)),
    ("Pão de hambúrguer", "un", "laticinios", 1.20, (30, 100)),
    ("Detergente", "un", "limpeza", 3.50, (10, 30)),
    ("Guardanapo", "dz", "limpeza", 4.00, (20, 60)),
    ("Papel toalha", "un", "limpeza", 6.50, (10, 30)),
]

# amplitude e mês de pico da curva sazonal, por categoria de fornecedor
SAZONALIDADE = {
    "hortifruti": (0.15, 2),
    "peixes": (0.12, 12),
    "bebidas": (0.10, 1),
    "carnes": (0.05, 12),
    "laticinios": (0.04, 6),
    "limpeza": (0.02, 6),
}

INFLACAO_MENSAL_BASE = 0.007  # ~8.7% ao ano

RECEITAS = [
    ("Picanha na Chapa", "Carnes", 68.90, 1,
     [("Picanha", 0.35), ("Batata", 0.25), ("Alface", 0.05)]),
    ("Frango Grelhado com Arroz e Feijão", "Aves", 32.90, 1,
     [("Peito de frango", 0.25), ("Arroz", 0.15), ("Feijão", 0.15)]),
    ("Salada Caesar com Frango", "Saladas", 28.50, 1,
     [("Alface", 0.15), ("Peito de frango", 0.12), ("Queijo mussarela", 0.05)]),
    ("Feijoada Completa", "Pratos Típicos", 39.90, 1,
     [("Feijão", 0.30), ("Costela bovina", 0.20), ("Linguiça", 0.15), ("Arroz", 0.15)]),
    ("Hambúrguer Artesanal de Picanha", "Lanches", 34.90, 1,
     [("Picanha", 0.18), ("Pão de hambúrguer", 1), ("Queijo mussarela", 0.04)]),
    ("Camarão ao Alho e Óleo", "Peixes e Frutos do Mar", 58.90, 1,
     [("Camarão", 0.25), ("Azeite de oliva", 0.03)]),
    ("Filé de Tilápia Grelhado", "Peixes e Frutos do Mar", 44.90, 1,
     [("Filé de tilápia", 0.30), ("Limão", 0.05), ("Batata", 0.20)]),
    ("Porção de Batata Frita", "Porções", 24.90, 2,
     [("Batata", 0.40)]),
    ("Linguiça Acebolada", "Porções", 26.90, 2,
     [("Linguiça", 0.30), ("Cebola", 0.15)]),
    ("Salada Tropical", "Saladas", 22.90, 1,
     [("Alface", 0.10), ("Tomate", 0.10), ("Cebola", 0.05)]),
]

DEMANDA_BASE = {
    "Picanha na Chapa": 8,
    "Frango Grelhado com Arroz e Feijão": 14,
    "Salada Caesar com Frango": 9,
    "Feijoada Completa": 5,
    "Hambúrguer Artesanal de Picanha": 16,
    "Camarão ao Alho e Óleo": 4,
    "Filé de Tilápia Grelhado": 6,
    "Porção de Batata Frita": 12,
    "Linguiça Acebolada": 7,
    "Salada Tropical": 6,
}

TABELAS_SEED = [
    "vendas",
    "receita_ingredientes",
    "receitas",
    "nota_linhas",
    "notas_fiscais",
    "produtos",
    "fornecedores",
]


def get_connection():
    load_dotenv()
    db_url = os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        raise SystemExit("SUPABASE_DB_URL não encontrado no .env")
    return psycopg2.connect(db_url)


def reset_tables(conn):
    with conn.cursor() as cur:
        for tabela in TABELAS_SEED:
            cur.execute(f"TRUNCATE TABLE restaurant.{tabela} RESTART IDENTITY CASCADE;")


def add_months(d, n):
    m = d.month - 1 + n
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, 1)


def month_range(n_months):
    fim = date.today().replace(day=1)
    inicio = add_months(fim, -(n_months - 1))
    return [add_months(inicio, i) for i in range(n_months)]


def insert_fornecedores(conn):
    with conn.cursor() as cur:
        ids = {}
        for f in FORNECEDORES:
            cur.execute(
                "INSERT INTO restaurant.fornecedores (nome, categoria, contato) "
                "VALUES (%s, %s, %s) RETURNING id",
                (f["nome"], f["categoria"], f["contato"]),
            )
            ids[f["nome"]] = cur.fetchone()[0]
    return {f["nome"]: (ids[f["nome"]], f["categoria"]) for f in FORNECEDORES}


def insert_produtos(conn):
    with conn.cursor() as cur:
        produtos = {}
        for nome, unidade, categoria, preco_base, faixa in PRODUTOS:
            cur.execute(
                "INSERT INTO restaurant.produtos (nome, unidade_medida, categoria) "
                "VALUES (%s, %s, %s) RETURNING id",
                (nome, unidade, categoria),
            )
            produto_id = cur.fetchone()[0]
            produtos[nome] = {
                "id": produto_id,
                "unidade": unidade,
                "categoria": categoria,
                "preco_base": preco_base,
                "faixa": faixa,
            }
    return produtos


def preco_do_mes(preco_base, categoria, mes_idx, mes_calendario, fornecedor_fator, rng):
    inflacao = (1 + INFLACAO_MENSAL_BASE) ** mes_idx
    amplitude, fase = SAZONALIDADE[categoria]
    sazonal = 1 + amplitude * math.sin(2 * math.pi * (mes_calendario - fase) / 12)
    ruido = rng.lognormal(mean=0, sigma=0.04)
    return round(preco_base * inflacao * sazonal * fornecedor_fator * ruido, 4)


def sorteia_quantidade(faixa, unidade, rng):
    qtd = rng.uniform(faixa[0], faixa[1])
    if unidade in ("kg", "L"):
        return round(qtd, 1)
    return float(round(qtd))


def generate_notas(conn, fornecedores, produtos, meses, rng):
    produtos_por_categoria = {}
    for nome, info in produtos.items():
        produtos_por_categoria.setdefault(info["categoria"], []).append(nome)

    fornecedor_fator = {nome: rng.normal(1.0, 0.05) for nome in fornecedores}

    total_notas = 0
    total_linhas = 0

    for mes_idx, mes_inicio in enumerate(meses):
        dias_no_mes = (add_months(mes_inicio, 1) - mes_inicio).days

        for nome_fornecedor, (fornecedor_id, categoria) in fornecedores.items():
            candidatos = produtos_por_categoria[categoria]
            n_compras = rng.integers(2, 5)

            for _ in range(n_compras):
                dia = int(rng.integers(1, dias_no_mes + 1))
                data_compra = mes_inicio + timedelta(days=dia - 1)

                n_itens = min(len(candidatos), int(rng.integers(3, 8)))
                itens = rng.choice(candidatos, size=n_itens, replace=False)

                linhas = []
                total = 0.0
                for nome_produto in itens:
                    info = produtos[nome_produto]
                    preco = preco_do_mes(
                        info["preco_base"], info["categoria"], mes_idx, mes_inicio.month,
                        fornecedor_fator[nome_fornecedor], rng,
                    )
                    qtd = sorteia_quantidade(info["faixa"], info["unidade"], rng)
                    linhas.append((info["id"], qtd, preco))
                    total += qtd * preco

                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO restaurant.notas_fiscais "
                        "(fornecedor_id, data, total, fonte) VALUES (%s, %s, %s, 'csv') "
                        "RETURNING id",
                        (fornecedor_id, data_compra, round(total, 2)),
                    )
                    nota_id = cur.fetchone()[0]

                execute_values(
                    conn.cursor(),
                    "INSERT INTO restaurant.nota_linhas "
                    "(nota_id, produto_id, quantidade, preco_unitario) VALUES %s",
                    [(nota_id, produto_id, qtd, preco) for produto_id, qtd, preco in linhas],
                )

                total_notas += 1
                total_linhas += len(linhas)

    return total_notas, total_linhas


def insert_receitas(conn):
    with conn.cursor() as cur:
        ids = {}
        for nome, categoria_menu, preco_venda, porcoes, _ in RECEITAS:
            cur.execute(
                "INSERT INTO restaurant.receitas (nome, preco_venda, categoria_menu, porcoes) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (nome, preco_venda, categoria_menu, porcoes),
            )
            ids[nome] = cur.fetchone()[0]
    return ids


def insert_receita_ingredientes(conn, receitas, produtos):
    linhas = []
    for nome, _, _, _, ingredientes in RECEITAS:
        receita_id = receitas[nome]
        for nome_produto, quantidade in ingredientes:
            linhas.append((receita_id, produtos[nome_produto]["id"], quantidade))

    execute_values(
        conn.cursor(),
        "INSERT INTO restaurant.receita_ingredientes (receita_id, produto_id, quantidade) VALUES %s",
        linhas,
    )


def demanda_do_dia(nome_receita, categoria_menu, data, mes_idx, rng):
    base = DEMANDA_BASE[nome_receita]
    crescimento = (1 + 0.004) ** mes_idx

    dia_semana = data.weekday()  # 0=segunda ... 6=domingo
    fator_semana = {0: 1.0, 1: 1.0, 2: 1.0, 3: 1.05, 4: 1.3, 5: 1.5, 6: 1.2}[dia_semana]

    fator_feijoada = 1.6 if (categoria_menu == "Pratos Típicos" and dia_semana == 5) else 1.0

    ruido = rng.lognormal(mean=0, sigma=0.15)
    lam = base * crescimento * fator_semana * fator_feijoada * ruido
    return max(lam, 0.1)


def generate_vendas(conn, receitas, meses, rng):
    linhas = []
    for mes_idx, mes_inicio in enumerate(meses):
        dias_no_mes = (add_months(mes_inicio, 1) - mes_inicio).days
        for dia in range(dias_no_mes):
            data_venda = mes_inicio + timedelta(days=dia)
            for nome, categoria_menu, _, _, _ in RECEITAS:
                lam = demanda_do_dia(nome, categoria_menu, data_venda, mes_idx, rng)
                unidades = rng.poisson(lam)
                if unidades > 0:
                    linhas.append((receitas[nome], data_venda, int(unidades)))

    execute_values(
        conn.cursor(),
        "INSERT INTO restaurant.vendas (receita_id, data, unidades) VALUES %s",
        linhas,
    )
    return len(linhas)


def main():
    parser = argparse.ArgumentParser(description="Gera dados sintéticos para o Restaurant Cost Analytics")
    parser.add_argument("--reset", action="store_true",
                         help="Apaga os dados existentes nas tabelas antes de gerar novos")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--months", type=int, default=12)
    args = parser.parse_args()

    random.seed(args.seed)
    rng = np.random.default_rng(args.seed)

    conn = get_connection()
    try:
        if args.reset:
            reset_tables(conn)

        fornecedores = insert_fornecedores(conn)
        produtos = insert_produtos(conn)
        meses = month_range(args.months)

        n_notas, n_linhas = generate_notas(conn, fornecedores, produtos, meses, rng)
        receitas = insert_receitas(conn)
        insert_receita_ingredientes(conn, receitas, produtos)
        n_vendas = generate_vendas(conn, receitas, meses, rng)

        conn.commit()
        print(f"{len(fornecedores)} fornecedores, {len(produtos)} produtos")
        print(f"{n_notas} notas fiscais, {n_linhas} linhas de nota")
        print(f"{len(receitas)} receitas, {n_vendas} registros de venda")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
