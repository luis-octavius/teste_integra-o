\c postgres

DROP DATABASE IF EXISTS ans_analytics;
CREATE DATABASE ans_analytics 
    WITH 
    ENCODING = 'UTF8'
    TEMPLATE = template0  -- Usar template0 para evitar erro de collation
    CONNECTION LIMIT = -1;

\c ans_analytics

-- 2. CRIAR EXTENSÕES
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 3. CRIAR TABELAS

-- TABELA 1: Cadastro de operadoras
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
    data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para cadastro_operadoras
CREATE INDEX idx_cadastro_uf ON cadastro_operadoras(uf);
CREATE INDEX idx_cadastro_razao_social ON cadastro_operadoras(razao_social);
CREATE INDEX idx_cadastro_modalidade ON cadastro_operadoras(modalidade);

-- Restrições
ALTER TABLE cadastro_operadoras 
ADD CONSTRAINT unique_registro_operadora UNIQUE (registro_operadora);

ALTER TABLE cadastro_operadoras 
ADD CONSTRAINT unique_cnpj UNIQUE (cnpj);

ALTER TABLE cadastro_operadoras 
ADD CONSTRAINT check_uf CHECK (uf ~ '^[A-Z]{2}$');

-- TABELA 2: Despesas consolidadas
CREATE TABLE despesas_consolidadas (
    id SERIAL PRIMARY KEY,
    reg_ans VARCHAR(20) NOT NULL,
    cd_conta_contabil VARCHAR(50) NOT NULL,
    ano INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    valor_despesas DECIMAL(20,2) NOT NULL,
    data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Restrições para despesas_consolidadas
ALTER TABLE despesas_consolidadas 
ADD CONSTRAINT check_ano CHECK (ano BETWEEN 2000 AND 2100);

ALTER TABLE despesas_consolidadas 
ADD CONSTRAINT check_trimestre CHECK (trimestre BETWEEN 1 AND 4);

ALTER TABLE despesas_consolidadas 
ADD CONSTRAINT unique_registro_conta_trimestre 
    UNIQUE (reg_ans, cd_conta_contabil, ano, trimestre);

-- Índices para despesas_consolidadas
CREATE INDEX idx_dc_reg_ans ON despesas_consolidadas(reg_ans);
CREATE INDEX idx_dc_ano_trimestre ON despesas_consolidadas(ano, trimestre);
CREATE INDEX idx_dc_conta ON despesas_consolidadas(cd_conta_contabil);
CREATE INDEX idx_dc_valor ON despesas_consolidadas(valor_despesas);

-- TABELA 3: Despesas agregadas
CREATE TABLE despesas_agregadas (
    id SERIAL PRIMARY KEY,
    razao_social VARCHAR(255) NOT NULL,
    uf CHAR(2) NOT NULL,
    total_despesas FLOAT NOT NULL,
    media_trimestral FLOAT NOT NULL,
    desvio_padrao FLOAT,
    coeficiente_variacao DECIMAL(10,2),
    data_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Restrição para despesas_agregadas
ALTER TABLE despesas_agregadas 
ADD CONSTRAINT check_uf_agregada CHECK (uf ~ '^[A-Z]{2}$');

-- Índices para despesas_agregadas
CREATE INDEX idx_da_razao_social ON despesas_agregadas(razao_social);
CREATE INDEX idx_da_uf ON despesas_agregadas(uf);
CREATE INDEX idx_da_total ON despesas_agregadas(total_despesas DESC);
CREATE INDEX idx_da_cv ON despesas_agregadas(coeficiente_variacao DESC);

-- =======================================================
-- IMPORTANTE: NÃO IMPORTAR DADOS AQUI!
-- A importação será feita pelo Python depois
-- =======================================================

-- 4. VIEWS PARA ANÁLISE

-- View: Operadoras com despesas
CREATE OR REPLACE VIEW vw_operadoras_com_despesas AS
SELECT 
    co.*,
    COALESCE(da.total_despesas, 0) AS total_despesas,
    COALESCE(da.media_trimestral, 0) AS media_trimestral,
    da.coeficiente_variacao
FROM cadastro_operadoras co
LEFT JOIN despesas_agregadas da 
    ON co.razao_social = da.razao_social AND co.uf = da.uf;

-- View: Análise por UF
CREATE OR REPLACE VIEW vw_analise_por_uf AS
SELECT 
    uf,
    COUNT(DISTINCT razao_social) AS qtd_operadoras,
    SUM(total_despesas) AS total_despesas_uf,
    AVG(total_despesas) AS media_despesas_por_operadora
FROM despesas_agregadas
WHERE uf IS NOT NULL AND uf != ''
GROUP BY uf
ORDER BY total_despesas_uf DESC;

-- View: Top 10 operadoras
CREATE OR REPLACE VIEW vw_top_operadoras AS
SELECT 
    razao_social,
    uf,
    total_despesas,
    media_trimestral,
    coeficiente_variacao,
    RANK() OVER (ORDER BY total_despesas DESC) AS ranking
FROM despesas_agregadas
ORDER BY total_despesas DESC
LIMIT 10;

-- 5. FUNÇÕES ÚTEIS

-- Função para formatar CNPJ
CREATE OR REPLACE FUNCTION formatar_cnpj(cnpj_input VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    IF cnpj_input IS NULL OR LENGTH(TRIM(cnpj_input)) < 14 THEN
        RETURN cnpj_input;
    END IF;
    
    RETURN SUBSTRING(cnpj_input FROM 1 FOR 2) || '.' ||
           SUBSTRING(cnpj_input FROM 3 FOR 3) || '.' ||
           SUBSTRING(cnpj_input FROM 6 FOR 3) || '/' ||
           SUBSTRING(cnpj_input FROM 9 FOR 4) || '-' ||
           SUBSTRING(cnpj_input FROM 13 FOR 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Função para classificar variabilidade
CREATE OR REPLACE FUNCTION classificar_variabilidade(cv DECIMAL)
RETURNS VARCHAR AS $$
BEGIN
    RETURN CASE 
        WHEN cv IS NULL OR cv = 0 THEN 'ESTAVEL'
        WHEN cv < 30 THEN 'BAIXA_VARIABILIDADE'
        WHEN cv < 60 THEN 'MEDIA_VARIABILIDADE'
        WHEN cv < 100 THEN 'ALTA_VARIABILIDADE'
        ELSE 'MUITO_ALTA_VARIABILIDADE'
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- 6. VERIFICAÇÃO FINAL

-- Mostrar tabelas criadas
\echo ' '
\echo '📊 TABELAS CRIADAS:'
SELECT 
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns 
     WHERE table_name = t.table_name) as colunas
FROM information_schema.tables t
WHERE table_schema = 'public'
ORDER BY table_name;

-- Mostrar índices criados
\echo ' '
\echo '⚡ ÍNDICES CRIADOS:'
SELECT 
    indexname,
    tablename
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Mostrar views criadas
\echo ' '
\echo '👁️  VIEWS CRIADAS:'
SELECT 
    table_name as view_name
FROM information_schema.views
WHERE table_schema = 'public'
ORDER BY table_name;

\echo ' '
\echo '========================================='
\echo '✅ BANCO DE DADOS CONFIGURADO COM SUCESSO!'
\echo '========================================='
\echo '📁 Banco: ans_analytics'
\echo '🔗 Conecte-se com: psql -U postgres -d ans_analytics'
\echo ' '
\echo '⚠️  IMPORTANTE: Os dados serão importados via Python'
\echo '   Execute: python scripts/import_data.py'
\echo '========================================='
