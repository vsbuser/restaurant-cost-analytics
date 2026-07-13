-- ============================================================
-- Restaurant Cost Analytics — Views (Etapa 4)
-- ============================================================

-- ---------------------------------------------------------------
-- vw_ultimo_preco_produto: preço da compra mais recente de cada produto.
-- Window function (ROW_NUMBER) particiona por produto e ordena por data
-- decrescente; rn = 1 é a compra mais recente daquele produto.
-- ---------------------------------------------------------------
CREATE OR REPLACE VIEW restaurant.vw_ultimo_preco_produto AS
SELECT produto_id, preco_unitario AS ultimo_preco, data_compra
FROM (
    SELECT
        nl.produto_id,
        nl.preco_unitario,
        nf.data AS data_compra,
        ROW_NUMBER() OVER (PARTITION BY nl.produto_id ORDER BY nf.data DESC, nl.id DESC) AS rn
    FROM restaurant.nota_linhas nl
    JOIN restaurant.notas_fiscais nf ON nf.id = nl.nota_id
) compras_ordenadas
WHERE rn = 1;

-- ---------------------------------------------------------------
-- vw_custo_receita: custo dinâmico de cada receita, somando
-- quantidade de cada ingrediente pelo último preço de compra.
-- ---------------------------------------------------------------
CREATE OR REPLACE VIEW restaurant.vw_custo_receita AS
SELECT
    r.id AS receita_id,
    r.nome,
    r.categoria_menu,
    r.porcoes,
    r.preco_venda,
    SUM(ri.quantidade * up.ultimo_preco) AS custo_total
FROM restaurant.receitas r
JOIN restaurant.receita_ingredientes ri ON ri.receita_id = r.id
JOIN restaurant.vw_ultimo_preco_produto up ON up.produto_id = ri.produto_id
GROUP BY r.id, r.nome, r.categoria_menu, r.porcoes, r.preco_venda;

-- ---------------------------------------------------------------
-- vw_food_cost: food cost % e semáforo (verde < 30%, amarelo 30–35%,
-- vermelho > 35%).
-- ---------------------------------------------------------------
CREATE OR REPLACE VIEW restaurant.vw_food_cost AS
SELECT
    receita_id,
    nome,
    categoria_menu,
    porcoes,
    preco_venda,
    custo_total,
    ROUND(100 * custo_total / preco_venda, 1) AS food_cost_pct,
    CASE
        WHEN 100 * custo_total / preco_venda < 30 THEN 'verde'
        WHEN 100 * custo_total / preco_venda <= 35 THEN 'amarelo'
        ELSE 'vermelho'
    END AS semaforo
FROM restaurant.vw_custo_receita;

-- ============================================================
-- Views (Etapa 5) — dashboard analítico
-- ============================================================

-- ---------------------------------------------------------------
-- vw_preco_medio_mensal: preço médio ponderado por produto/mês
-- (ponderado pela quantidade comprada em cada nota, não uma média simples).
-- ---------------------------------------------------------------
CREATE OR REPLACE VIEW restaurant.vw_preco_medio_mensal AS
SELECT
    nl.produto_id,
    p.nome AS produto,
    date_trunc('month', nf.data)::date AS mes,
    SUM(nl.quantidade * nl.preco_unitario) / SUM(nl.quantidade) AS preco_medio_ponderado
FROM restaurant.nota_linhas nl
JOIN restaurant.notas_fiscais nf ON nf.id = nl.nota_id
JOIN restaurant.produtos p ON p.id = nl.produto_id
GROUP BY nl.produto_id, p.nome, date_trunc('month', nf.data);

-- ---------------------------------------------------------------
-- vw_variacao_preco: compara a compra mais recente de cada produto com a
-- anterior; alerta = true se o preço subiu mais de 10%.
-- ---------------------------------------------------------------
CREATE OR REPLACE VIEW restaurant.vw_variacao_preco AS
WITH compras_numeradas AS (
    SELECT
        nl.produto_id,
        nl.preco_unitario,
        nf.data,
        nf.fornecedor_id,
        ROW_NUMBER() OVER (PARTITION BY nl.produto_id ORDER BY nf.data DESC, nl.id DESC) AS rn
    FROM restaurant.nota_linhas nl
    JOIN restaurant.notas_fiscais nf ON nf.id = nl.nota_id
)
SELECT
    atual.produto_id,
    p.nome AS produto,
    f.nome AS fornecedor,
    anterior.preco_unitario AS preco_anterior,
    atual.preco_unitario AS preco_atual,
    ROUND(100.0 * (atual.preco_unitario - anterior.preco_unitario) / anterior.preco_unitario, 1) AS variacao_pct,
    (atual.preco_unitario - anterior.preco_unitario) / anterior.preco_unitario > 0.10 AS alerta
FROM compras_numeradas atual
JOIN compras_numeradas anterior
    ON anterior.produto_id = atual.produto_id AND anterior.rn = atual.rn + 1
JOIN restaurant.produtos p ON p.id = atual.produto_id
JOIN restaurant.fornecedores f ON f.id = atual.fornecedor_id
WHERE atual.rn = 1;
