-- ============================================================
-- Restaurant Cost Analytics — Schema (Etapa 1)
-- Schema dedicado para isolar do namespace padrão do Supabase
-- ============================================================

CREATE SCHEMA IF NOT EXISTS restaurant;

-- ---------------------------------------------------------------
-- fornecedores: quem vende os insumos
-- ---------------------------------------------------------------
CREATE TABLE restaurant.fornecedores (
    id          BIGSERIAL PRIMARY KEY,
    nome        TEXT NOT NULL,
    categoria   TEXT,
    contato     TEXT,
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------
-- produtos: catálogo de insumos/ingredientes.
-- Sem coluna de preço: preço é histórico e vive em nota_linhas.
-- ---------------------------------------------------------------
CREATE TABLE restaurant.produtos (
    id              BIGSERIAL PRIMARY KEY,
    nome            TEXT NOT NULL,
    unidade_medida  TEXT NOT NULL CHECK (unidade_medida IN ('kg', 'g', 'L', 'ml', 'un', 'cx', 'dz')),
    categoria       TEXT,
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (nome, unidade_medida)
);

-- ---------------------------------------------------------------
-- notas_fiscais: cabeçalho de cada compra de um fornecedor
-- ---------------------------------------------------------------
CREATE TABLE restaurant.notas_fiscais (
    id             BIGSERIAL PRIMARY KEY,
    fornecedor_id  BIGINT NOT NULL REFERENCES restaurant.fornecedores(id),
    data           DATE NOT NULL,
    total          NUMERIC(10,2) NOT NULL CHECK (total >= 0),
    fonte          TEXT NOT NULL CHECK (fonte IN ('foto_ia', 'manual', 'csv')),
    foto_url       TEXT,
    criado_em      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_notas_fiscais_fornecedor ON restaurant.notas_fiscais(fornecedor_id);
CREATE INDEX idx_notas_fiscais_data ON restaurant.notas_fiscais(data);

-- ---------------------------------------------------------------
-- nota_linhas: itens de cada nota. Aqui vive o histórico de preços
-- usado depois para preço médio ponderado e custo dinâmico de receitas.
-- ---------------------------------------------------------------
CREATE TABLE restaurant.nota_linhas (
    id              BIGSERIAL PRIMARY KEY,
    nota_id         BIGINT NOT NULL REFERENCES restaurant.notas_fiscais(id) ON DELETE CASCADE,
    produto_id      BIGINT NOT NULL REFERENCES restaurant.produtos(id),
    quantidade      NUMERIC(10,3) NOT NULL CHECK (quantidade > 0),
    preco_unitario  NUMERIC(10,4) NOT NULL CHECK (preco_unitario >= 0)
);

CREATE INDEX idx_nota_linhas_nota ON restaurant.nota_linhas(nota_id);
CREATE INDEX idx_nota_linhas_produto ON restaurant.nota_linhas(produto_id);

-- ---------------------------------------------------------------
-- receitas: fichas técnicas (pratos do menu)
-- ---------------------------------------------------------------
CREATE TABLE restaurant.receitas (
    id              BIGSERIAL PRIMARY KEY,
    nome            TEXT NOT NULL,
    preco_venda     NUMERIC(10,2) NOT NULL CHECK (preco_venda >= 0),
    categoria_menu  TEXT,
    porcoes         INTEGER NOT NULL DEFAULT 1 CHECK (porcoes > 0),
    criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------
-- receita_ingredientes: composição de cada receita (M:N produtos <-> receitas)
-- ---------------------------------------------------------------
CREATE TABLE restaurant.receita_ingredientes (
    id          BIGSERIAL PRIMARY KEY,
    receita_id  BIGINT NOT NULL REFERENCES restaurant.receitas(id) ON DELETE CASCADE,
    produto_id  BIGINT NOT NULL REFERENCES restaurant.produtos(id),
    quantidade  NUMERIC(10,3) NOT NULL CHECK (quantidade > 0),
    UNIQUE (receita_id, produto_id)
);

CREATE INDEX idx_receita_ingredientes_receita ON restaurant.receita_ingredientes(receita_id);
CREATE INDEX idx_receita_ingredientes_produto ON restaurant.receita_ingredientes(produto_id);

-- ---------------------------------------------------------------
-- vendas: histórico de vendas por prato, para análise de demanda
-- ---------------------------------------------------------------
CREATE TABLE restaurant.vendas (
    id          BIGSERIAL PRIMARY KEY,
    receita_id  BIGINT NOT NULL REFERENCES restaurant.receitas(id),
    data        DATE NOT NULL,
    unidades    INTEGER NOT NULL CHECK (unidades > 0)
);

CREATE INDEX idx_vendas_receita ON restaurant.vendas(receita_id);
CREATE INDEX idx_vendas_data ON restaurant.vendas(data);
