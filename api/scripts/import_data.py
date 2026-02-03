#!/usr/bin/env python3
"""
Script para importar dados CSV para o banco PostgreSQL
"""
import os
import sys
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE_DIR, "csv")

# Arquivos CSV esperados
CSV_FILES = {
    "cadastro": "Relatorio_cadop.csv",
    "consolidado": "consolidado_despesas.csv", 
    "agregado": "despesas_agregadas.csv"
}

# Configuração do banco
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ans_analytics"

def setup_database():
    """Conectar ao banco e criar engine"""
    try:
        engine = create_engine(DATABASE_URL)
        # Testar conexão
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Conexão com banco de dados estabelecida")
        return engine
    except Exception as e:
        logger.error(f"❌ Erro ao conectar ao banco: {e}")
        sys.exit(1)

def import_cadastro(engine):
    """Importar dados cadastrais das operadoras"""
    csv_path = os.path.join(CSV_DIR, CSV_FILES["cadastro"])
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  Arquivo não encontrado: {csv_path}")
        logger.info("Pulando importação de cadastro...")
        return
    
    try:
        logger.info(f"📥 Importando cadastro de: {csv_path}")
        
        # Ler CSV com encoding correto
        df = pd.read_csv(
            csv_path,
            sep=';',
            encoding='utf-8',
            dtype=str,
            na_filter=False
        )
        
        logger.info(f"📄 Total de registros: {len(df)}")
        
        # Renomear colunas para padronizar
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Mapear nomes de colunas
        column_mapping = {
            'registro_operadora': 'registro_operadora',
            'cnpj': 'cnpj',
            'razao_social': 'razao_social',
            'nome_fantasia': 'nome_fantasia',
            'modalidade': 'modalidade',
            'logradouro': 'logradouro',
            'numero': 'numero',
            'complemento': 'complemento',
            'bairro': 'bairro',
            'cidade': 'cidade',
            'uf': 'uf',
            'cep': 'cep',
            'ddd': 'ddd',
            'telefone': 'telefone',
            'fax': 'fax',
            'endereco_eletronico': 'endereco_eletronico',
            'representante': 'representante',
            'cargo_representante': 'cargo_representante',
            'regiao_de_comercializacao': 'regiao_de_comercializacao',
            'data_registro_ans': 'data_registro_ans'
        }
        
        # Renomear colunas
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Limpar e converter regiao_de_comercializacao
        if 'regiao_de_comercializacao' in df.columns:
            df['regiao_de_comercializacao'] = pd.to_numeric(df['regiao_de_comercializacao'], errors='coerce').astype('Int64')

        # Limpar dados
        df['cnpj'] = df['cnpj'].astype(str).str.replace(r'\D', '', regex=True)
        df['uf'] = df['uf'].astype(str).str.upper().str.strip()
        df['razao_social'] = df['razao_social'].astype(str).str.strip()
        
        # Converter data
        def parse_date(date_str):
            if pd.isna(date_str) or str(date_str).strip() == '':
                return None
            try:
                # Tentar formato YYYY-MM-DD
                return pd.to_datetime(date_str, format='%Y-%m-%d')
            except:
                try:
                    # Tentar formato DD/MM/YYYY
                    return pd.to_datetime(date_str, format='%d/%m/%Y')
                except:
                    return None
        
        df['data_registro_ans'] = df['data_registro_ans'].apply(parse_date)
        
        # Inserir no banco
        df.to_sql(
            'cadastro_operadoras',
            engine,
            if_exists='append',
            index=False,
            chunksize=1000
        )
        
        logger.info(f"✅ Cadastro importado: {len(df)} registros")
        
    except Exception as e:
        logger.error(f"❌ Erro ao importar cadastro: {e}")
        raise

def import_consolidado(engine):
    """Importar despesas consolidadas"""
    csv_path = os.path.join(CSV_DIR, CSV_FILES["consolidado"])
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  Arquivo não encontrado: {csv_path}")
        logger.info("Pulando importação de despesas consolidadas...")
        return
    
    try:
        logger.info(f"📥 Importando despesas consolidadas: {csv_path}")
        
        # Ler CSV
        df = pd.read_csv(
            csv_path,
            sep=';',
            encoding='utf-8',
            dtype=str,
            na_filter=False
        )
        
        logger.info(f"📄 Total de registros: {len(df)}")
        
        # Verificar colunas
        required_columns = ['REG_ANS', 'CD_CONTA_CONTABIL', 'ANO', 'TRIMESTRE', 'VALOR_DESPESAS']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            logger.error(f"❌ Colunas faltando: {missing_columns}")
            return
        
        # Renomear colunas para minúsculas
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Limpar e converter dados
        df['reg_ans'] = df['reg_ans'].astype(str).str.strip()
        df['cd_conta_contabil'] = df['cd_conta_contabil'].astype(str).str.strip()
        
        # Converter ano e trimestre
        df['ano'] = pd.to_numeric(df['ano'], errors='coerce').fillna(0).astype(int)
        df['trimestre'] = pd.to_numeric(df['trimestre'], errors='coerce').fillna(0).astype(int)
        
        # Converter valor_despesas (formato brasileiro: 1.000,50)
        def convert_br_currency(value):
            if pd.isna(value) or str(value).strip() == '':
                return 0.0
            try:
                # Remover pontos de milhar, substituir vírgula decimal
                value_str = str(value).replace('.', '').replace(',', '.')
                return float(value_str)
            except:
                return 0.0
        
        df['valor_despesas'] = df['valor_despesas'].apply(convert_br_currency)
        
        # Filtrar registros inválidos
        df = df[
            (df['reg_ans'] != '') & 
            (df['cd_conta_contabil'] != '') &
            (df['ano'] >= 2000) &
            (df['trimestre'].between(1, 4)) &
            (df['valor_despesas'] != 0)
        ]

        # Remove duplicates
        df = df.drop_duplicates(subset=['reg_ans', 'cd_conta_contabil', 'ano', 'trimestre'], keep='first')
        
        logger.info(f"📊 Registros válidos: {len(df)}")
        
        # Inserir no banco
        df.to_sql(
            'despesas_consolidadas',
            engine,
            if_exists='append',
            index=False,
            chunksize=5000
        )
        
        logger.info(f"✅ Despesas consolidadas importadas: {len(df)} registros")
        
    except Exception as e:
        logger.error(f"❌ Erro ao importar despesas consolidadas: {e}")
        raise

def import_agregado(engine):
    """Importar despesas agregadas"""
    csv_path = os.path.join(CSV_DIR, CSV_FILES["agregado"])
    
    if not os.path.exists(csv_path):
        logger.warning(f"⚠️  Arquivo não encontrado: {csv_path}")
        logger.info("Pulando importação de despesas agregadas...")
        return
    
    try:
        logger.info(f"📥 Importando despesas agregadas: {csv_path}")
        
        # Ler CSV
        df = pd.read_csv(
            csv_path,
            sep=';',
            encoding='utf-8',
            dtype=str,
            na_filter=False
        )
        
        logger.info(f"📄 Total de registros: {len(df)}")
        
        # Renomear colunas para minúsculas
        df.columns = [col.strip().lower() for col in df.columns]
        
        # Mapear nomes de colunas
        column_mapping = {
            'razao_social': 'razao_social',
            'uf': 'uf',
            'total_despesas': 'total_despesas',
            'media_trimestral': 'media_trimestral',
            'desvio_padrao': 'desvio_padrao',
            'coeficiente_variacao': 'coeficiente_variacao'
        }
        
        # Renomear colunas
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        # Limpar dados
        df['razao_social'] = df['razao_social'].astype(str).str.strip()
        df['uf'] = df['uf'].astype(str).str.upper().str.strip()
        
        # Converter valores numéricos
        def convert_numeric(value):
            if pd.isna(value) or str(value).strip() == '':
                return None
            try:
                # Formato brasileiro: 1.000,50
                value_str = str(value).replace('.', '').replace(',', '.')
                return float(value_str)
            except:
                return None
        
        numeric_columns = ['total_despesas', 'media_trimestral', 'desvio_padrao', 'coeficiente_variacao']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(convert_numeric)
        
        # Filtrar registros inválidos
        df = df[
            (df['razao_social'] != '') &
            (df['uf'].str.len() == 2) &
            (df['total_despesas'].notna()) &
            (df['media_trimestral'].notna())
        ]
        
        logger.info(f"📊 Registros válidos: {len(df)}")
        
        # Inserir no banco
        df.to_sql(
            'despesas_agregadas',
            engine,
            if_exists='append',
            index=False
        )
        
        logger.info(f"✅ Despesas agregadas importadas: {len(df)} registros")
        
    except Exception as e:
        logger.error(f"❌ Erro ao importar despesas agregadas: {e}")
        raise

def main():
    """Função principal"""
    print("=" * 60)
    print("📊 IMPORTADOR DE DADOS - ANS ANALYTICS")
    print("=" * 60)
    
    # Verificar diretório CSV
    if not os.path.exists(CSV_DIR):
        logger.error(f"❌ Diretório CSV não encontrado: {CSV_DIR}")
        logger.info("Crie o diretório e coloque os arquivos CSV nele:")
        logger.info(f"  mkdir -p {CSV_DIR}")
        logger.info("  cp *.csv {CSV_DIR}/")
        sys.exit(1)
    
    # Conectar ao banco
    engine = setup_database()
    
    # Importar dados
    try:
        import_cadastro(engine)
        import_consolidado(engine)
        import_agregado(engine)
        
        print("\n" + "=" * 60)
        print("🎉 IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        
        # Estatísticas finais
        with engine.connect() as conn:
            # Contar registros
            tables = ['cadastro_operadoras', 'despesas_consolidadas', 'despesas_agregadas']
            for table in tables:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"📋 {table}: {count:,} registros")
        
        print("\n✅ Pronto! O banco está populado e pronto para uso.")
        print("🔗 API: http://localhost:8000")
        print("📊 Docs: http://localhost:8000/docs")
        
    except Exception as e:
        logger.error(f"❌ Erro durante a importação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
