"""
Configurações para o importador
"""
import os

# Diretórios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE_DIR, "csv")
SQL_DIR = os.path.join(BASE_DIR, "scripts")
DATA_DIR = os.path.join(BASE_DIR, "data")

# Banco de dados
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "ans_analytics",
    "user": "postgres",
    "password": "postgres"  # Altere para sua senha
}

# Arquivos CSV esperados
CSV_FILES = {
    "cadastro": {
        "filename": "Relatorio_cadop.csv",
        "columns": [
            "REGISTRO_OPERADORA", "CNPJ", "Razao_Social", "Nome_Fantasia", "Modalidade",
            "Logradouro", "Numero", "Complemento", "Bairro", "Cidade", "UF", "CEP",
            "DDD", "Telefone", "Fax", "Endereco_eletronico", "Representante",
            "Cargo_Representante", "Regiao_de_Comercializacao", "Data_Registro_ANS"
        ],
        "separator": ";",
        "encoding": "utf-8"
    },
    "consolidado": {
        "filename": "consolidado_despesas.csv",
        "columns": ["REG_ANS", "CD_CONTA_CONTABIL", "ANO", "TRIMESTRE", "VALOR_DESPESAS"],
        "separator": ";",
        "encoding": "utf-8"
    },
    "agregado": {
        "filename": "despesas_agregadas.csv",
        "columns": ["Razao_Social", "UF", "TOTAL_DESPESAS", "MEDIA_TRIMESTRAL", 
                   "DESVIO_PADRAO", "COEFICIENTE_VARIACAO"],
        "separator": ";",
        "encoding": "utf-8"
    }
}

# Configurações de importação
IMPORT_CONFIG = {
    "chunk_size": 10000,
    "max_errors": 100,
    "skip_invalid": True,
    "log_errors": True
}
