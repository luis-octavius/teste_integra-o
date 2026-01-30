CREATE DATABASE ans_analytics
    WITH 
    ENCODING = 'UTF8'
    LC_COLLATE = 'pt_BR.UTF-8'
    LC_CTYPE = 'pt_BR.UTF-8'
    CONNECTION LIMIT = -1;

\c ans_analytics;

-- TABELA 1: Cadastro de operadoras (relatorio_cadop.csv)
CREATE TABLE cadastro_operadoras (
    id SERIAL PRIMARY KEY,
    registro_operadora VARCHAR(20) NOT NULL,
    cnpj VARCHAR(20) NOT NULL,
    razao_social VARCHAR(255) NOT NULL,
    nome_fantasia VARCHAR(255),
    modalidade VARCHAR(100),
    logradouro VARCHAR(255),
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    uf CHAR(2) NOT NULL,
    cep VARCHAR(10),
    ddd VARCHAR(3),
    telefone VARCHAR(20),
    fax VARCHAR(20),
    endereco_eletronico VARCHAR(255),
    representante VARCHAR(255),
    cargo_representante VARCHAR(100),
    regiao_de_comercializacao INTEGER,
    data_registro_ans DATE,
    data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices
    CONSTRAINT check_uf CHECK (uf ~ '^[A-Z]{2}$'),
    CONSTRAINT unique_registro_operadora UNIQUE (registro_operadora),
    CONSTRAINT unique_cnpj UNIQUE (cnpj)
);

CREATE INDEX idx_cadastro_uf ON cadastro_operadoras(uf);
CREATE INDEX idx_cadastro_razao_social ON cadastro_operadoras(razao_social);
CREATE INDEX idx_cadastro_modalidade ON cadastro_operadoras(modalidade);

-- TABELA 2: Despesas consolidadas (consolidado_despesas.csv)
CREATE TABLE despesas_consolidadas (
    id SERIAL PRIMARY KEY,
    reg_ans VARCHAR(20) NOT NULL,
    cd_conta_contabil VARCHAR(50) NOT NULL,
    ano INTEGER NOT NULL CHECK (ano BETWEEN 2000 AND 2100),
    trimestre INTEGER NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    valor_despesas DECIMAL(15,2) NOT NULL,
    data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices
    CONSTRAINT unique_registro_conta_trimestre 
        UNIQUE (reg_ans, cd_conta_contabil, ano, trimestre)
);

CREATE INDEX idx_dc_reg_ans ON despesas_consolidadas(reg_ans);
CREATE INDEX idx_dc_ano_trimestre ON despesas_consolidadas(ano, trimestre);
CREATE INDEX idx_dc_conta ON despesas_consolidadas(cd_conta_contabil);
CREATE INDEX idx_dc_valor ON despesas_consolidadas(valor_despesas);

-- TABELA 3: Despesas agregadas (despesas_agregadas.csv)
CREATE TABLE despesas_agregadas (
    id SERIAL PRIMARY KEY,
    razao_social VARCHAR(255) NOT NULL,
    uf CHAR(2) NOT NULL,
    total_despesas DECIMAL(15,2) NOT NULL,
    media_trimestral DECIMAL(15,2) NOT NULL,
    desvio_padrao DECIMAL(15,2),
    coeficiente_variacao DECIMAL(10,2),
    data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Índices
    CONSTRAINT check_uf_agregada CHECK (uf ~ '^[A-Z]{2}$')
);

CREATE INDEX idx_da_razao_social ON despesas_agregadas(razao_social);
CREATE INDEX idx_da_uf ON despesas_agregadas(uf);
CREATE INDEX idx_da_total ON despesas_agregadas(total_despesas DESC);
CREATE INDEX idx_da_cv ON despesas_agregadas(coeficiente_variacao DESC);



-- IMPORTAR CADASTRO (relatorio_cadop.csv)
COPY cadastro_operadoras (
    registro_operadora, cnpj, razao_social, nome_fantasia, modalidade,
    logradouro, numero, complemento, bairro, cidade, uf, cep,
    ddd, telefone, fax, endereco_eletronico, representante, 
    cargo_representante, regiao_de_comercializacao, data_registro_ans
)

FROM './../csv/Relatorio_cadop.csv'
WITH (
    FORMAT csv,
    DELIMITER ';',
    HEADER true,
    ENCODING 'UTF8',
    NULL ''
);

-- TRATAMENTO DE INCONSISTÊNCIAS NO CADASTRO
UPDATE cadastro_operadoras 
SET 
    -- Normalizar CNPJ (apenas números)
    cnpj = REGEXP_REPLACE(cnpj, '[^0-9]', '', 'g'),
    
    -- Normalizar UF (maiúsculas, 2 caracteres)
    uf = UPPER(TRIM(uf)),
    
    -- Corrigir UF inválida
    uf = CASE 
        WHEN LENGTH(uf) = 2 AND uf ~ '^[A-Z]{2}$' THEN uf
        ELSE 'ND'  -- Não definido
    END,
    
    -- Limpar e validar data
    data_registro_ans = CASE 
        WHEN data_registro_ans ~ '^\d{4}-\d{2}-\d{2}$' 
            THEN TO_DATE(data_registro_ans, 'YYYY-MM-DD')
        WHEN data_registro_ans ~ '^\d{2}/\d{2}/\d{4}$' 
            THEN TO_DATE(data_registro_ans, 'DD/MM/YYYY')
        ELSE NULL 
    END,
    
    -- Normalizar telefone (apenas números)
    telefone = REGEXP_REPLACE(telefone, '[^0-9]', '', 'g'),
    ddd = REGEXP_REPLACE(ddd, '[^0-9]', '', 'g')
WHERE TRUE;

-- REMOVER REGISTROS INVÁLIDOS (CNPJ obrigatório)
DELETE FROM cadastro_operadoras 
WHERE cnpj IS NULL OR LENGTH(TRIM(cnpj)) < 14;

-- IMPORTAR DESPESAS CONSOLIDADAS (consolidado_despesas.csv)
-- Tabela temporária para limpeza
CREATE TEMPORARY TABLE temp_consolidado (
    reg_ans VARCHAR(20),
    cd_conta_contabil VARCHAR(50),
    ano INTEGER,
    trimestre INTEGER,
    valor_despesas_text VARCHAR(50)
) ON COMMIT DROP;

COPY temp_consolidado 
FROM './../csv/consolidado_despesas.csv'
WITH (
    FORMAT csv,
    DELIMITER ';',
    HEADER true,
    ENCODING 'UTF8',
    NULL ''
);

-- TRATAMENTO E INSERÇÃO
INSERT INTO despesas_consolidadas (
    reg_ans, cd_conta_contabil, ano, trimestre, valor_despesas
)
SELECT 
    -- Limpar e validar registro ANS
    REGEXP_REPLACE(TRIM(reg_ans), '[^0-9]', '', 'g') AS reg_ans,
    
    -- Limpar código da conta
    TRIM(cd_conta_contabil) AS cd_conta_contabil,
    
    -- Validar ano
    CASE 
        WHEN ano BETWEEN 2000 AND EXTRACT(YEAR FROM CURRENT_DATE) 
        THEN ano
        ELSE EXTRACT(YEAR FROM CURRENT_DATE) - 1
    END AS ano,
    
    -- Validar trimestre
    CASE 
        WHEN trimestre BETWEEN 1 AND 4 THEN trimestre
        ELSE 1
    END AS trimestre,
    
    -- Converter valor (formato brasileiro: 1.000,50)
    CASE 
        WHEN valor_despesas_text ~ '^-?\d{1,3}(\.\d{3})*,\d{2}$'  -- Formato BR
            THEN REPLACE(REPLACE(valor_despesas_text, '.', ''), ',', '.')::DECIMAL
        WHEN valor_despesas_text ~ '^-?\d+(\.\d{2})?$'  -- Formato padrão
            THEN valor_despesas_text::DECIMAL
        ELSE 0.00
    END AS valor_despesas
    
FROM temp_consolidado
WHERE 
    -- Filtrar registros válidos
    reg_ans IS NOT NULL 
    AND TRIM(reg_ans) != ''
    AND cd_conta_contabil IS NOT NULL
    AND TRIM(cd_conta_contabil) != ''
    AND valor_despesas_text IS NOT NULL
    AND TRIM(valor_despesas_text) != '';

-- IMPORTAR DESPESAS AGREGADAS (despesas_agregadas.csv)
COPY despesas_agregadas (
    razao_social, uf, total_despesas, media_trimestral, 
    desvio_padrao, coeficiente_variacao
)
FROM './../csv/despesas_agregadas.csv'
WITH (
    FORMAT csv,
    DELIMITER ';',
    HEADER true,
    ENCODING 'UTF8',
    NULL ''
);

-- TRATAMENTO DAS DESPESAS AGREGADAS
UPDATE despesas_agregadas 
SET 
    -- Normalizar UF
    uf = UPPER(TRIM(uf)),
    uf = CASE 
        WHEN LENGTH(uf) = 2 AND uf ~ '^[A-Z]{2}$' THEN uf
        ELSE 'ND'
    END,
    
    -- Limpar e converter valores
    total_despesas = CASE 
        WHEN total_despesas IS NOT NULL THEN total_despesas
        ELSE 0.00
    END,
    
    media_trimestral = CASE 
        WHEN media_trimestral IS NOT NULL THEN media_trimestral
        ELSE 0.00
    END,
    
    -- Calcular coeficiente de variação se não existir
    coeficiente_variacao = CASE 
        WHEN coeficiente_variacao IS NOT NULL THEN coeficiente_variacao
        WHEN desvio_padrao IS NOT NULL AND media_trimestral > 0 
            THEN (desvio_padrao / media_trimestral) * 100
        ELSE NULL
    END
WHERE TRUE;

-- -------------------------------------------------------
-- 3.4. QUERIES ANALÍTICAS (USANDO AS TABELAS EXATAS)
-- -------------------------------------------------------

-- QUERY 1: 5 operadoras com maior crescimento percentual de despesas
-- entre o primeiro e o último trimestre analisado

-- PRIMEIRO: Identificar primeiro e último trimestre disponíveis
WITH periodos AS (
    SELECT 
        MIN(CONCAT(ano, '-', trimestre)) AS primeiro_periodo,
        MAX(CONCAT(ano, '-', trimestre)) AS ultimo_periodo,
        MIN(ano) AS primeiro_ano,
        MIN(trimestre) AS primeiro_trimestre,
        MAX(ano) AS ultimo_ano,
        MAX(trimestre) AS ultimo_trimestre
    FROM despesas_consolidadas
),
-- SEGUNDO: Buscar dados do primeiro trimestre
primeiro_trimestre AS (
    SELECT 
        dc.reg_ans,
        COALESCE(co.razao_social, 'OPERADORA NÃO CADASTRADA') AS razao_social,
        SUM(dc.valor_despesas) AS despesa_inicial
    FROM despesas_consolidadas dc
    LEFT JOIN cadastro_operadoras co ON dc.reg_ans = co.registro_operadora
    CROSS JOIN periodos p
    WHERE dc.ano = p.primeiro_ano AND dc.trimestre = p.primeiro_trimestre
    GROUP BY dc.reg_ans, co.razao_social
),
-- TERCEIRO: Buscar dados do último trimestre
ultimo_trimestre AS (
    SELECT 
        dc.reg_ans,
        COALESCE(co.razao_social, 'OPERADORA NÃO CADASTRADA') AS razao_social,
        SUM(dc.valor_despesas) AS despesa_final
    FROM despesas_consolidadas dc
    LEFT JOIN cadastro_operadoras co ON dc.reg_ans = co.registro_operadora
    CROSS JOIN periodos p
    WHERE dc.ano = p.ultimo_ano AND dc.trimestre = p.ultimo_trimestre
    GROUP BY dc.reg_ans, co.razao_social
),
-- QUARTO: Calcular crescimento
crescimento_calculado AS (
    SELECT 
        COALESCE(pt.razao_social, ut.razao_social) AS razao_social,
        COALESCE(pt.reg_ans, ut.reg_ans) AS registro_ans,
        pt.despesa_inicial,
        ut.despesa_final,
        -- TRATAMENTO PARA DADOS FALTANTES:
        -- 1. Se não tem dado inicial mas tem final: é nova operadora
        -- 2. Se não tem dado final mas tem inicial: ficou inativa
        -- 3. Se tem ambos: calcular crescimento normal
        CASE 
            WHEN pt.despesa_inicial IS NULL AND ut.despesa_final IS NOT NULL 
                THEN 100.00  -- Nova operadora (crescimento máximo)
            WHEN pt.despesa_inicial = 0 AND ut.despesa_final > 0 
                THEN 100.00  -- Saiu de zero
            WHEN pt.despesa_inicial IS NOT NULL AND ut.despesa_final IS NOT NULL 
                THEN ROUND(
                    ((ut.despesa_final - pt.despesa_inicial) / 
                     NULLIF(pt.despesa_inicial, 0)) * 100, 
                    2
                )
            ELSE NULL
        END AS crescimento_percentual,
        CASE 
            WHEN pt.despesa_inicial IS NULL THEN 'NOVA'
            WHEN ut.despesa_final IS NULL THEN 'INATIVA'
            WHEN pt.despesa_inicial = 0 THEN 'INICIO_ZERO'
            ELSE 'ATIVA'
        END AS status_operadora
    FROM primeiro_trimestre pt
    FULL OUTER JOIN ultimo_trimestre ut ON pt.reg_ans = ut.reg_ans
    WHERE 
        (pt.despesa_inicial IS NOT NULL OR ut.despesa_final IS NOT NULL)
        AND COALESCE(pt.despesa_inicial, 0) >= 0
        AND COALESCE(ut.despesa_final, 0) >= 0
)
-- QUINTO: Resultado final
SELECT 
    registro_ans,
    razao_social,
    ROUND(COALESCE(despesa_inicial, 0)::numeric, 2) AS despesa_primeiro_trimestre,
    ROUND(COALESCE(despesa_final, 0)::numeric, 2) AS despesa_ultimo_trimestre,
    crescimento_percentual,
    status_operadora,
    -- Classificação do crescimento
    CASE 
        WHEN crescimento_percentual IS NULL THEN 'INDEFINIDO'
        WHEN crescimento_percentual > 100 THEN 'CRESCIMENTO_EXPONENCIAL'
        WHEN crescimento_percentual > 50 THEN 'ALTO_CRESCIMENTO'
        WHEN crescimento_percentual > 20 THEN 'MODERADO_CRESCIMENTO'
        WHEN crescimento_percentual > 0 THEN 'PEQUENO_CRESCIMENTO'
        WHEN crescimento_percentual = 0 THEN 'ESTAVEL'
        ELSE 'DECRESCIMENTO'
    END AS classificacao_crescimento
FROM crescimento_calculado
WHERE crescimento_percentual IS NOT NULL
ORDER BY crescimento_percentual DESC NULLS LAST
LIMIT 5;

-- QUERY 2: Distribuição de despesas por UF
-- Listar os 5 estados com maiores despesas totais

WITH despesas_por_uf AS (
    SELECT 
        da.uf,
        COUNT(DISTINCT da.razao_social) AS quantidade_operadoras,
        SUM(da.total_despesas) AS total_despesas_estado,
        AVG(da.total_desp
