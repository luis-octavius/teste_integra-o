"""
Modelos SQLAlchemy para o banco de dados
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Numeric
from datetime import datetime
from app.api.database import Base  # Importar Base de database.py


class Operadora(Base):
    __tablename__ = 'cadastro_operadoras'
    
    id = Column(Integer, primary_key=True, index=True)
    registro_operadora = Column(String(20), unique=True, nullable=False, index=True)
    cnpj = Column(String(20), unique=True, nullable=False, index=True)
    razao_social = Column(String(255), nullable=False, index=True)
    nome_fantasia = Column(String(255))
    modalidade = Column(String(100), index=True)
    logradouro = Column(String(255))
    numero = Column(String(20))
    complemento = Column(String(100))
    bairro = Column(String(100))
    cidade = Column(String(100))
    uf = Column(String(2), nullable=False, index=True)
    cep = Column(String(10))
    ddd = Column(String(3))
    telefone = Column(String(20))
    fax = Column(String(20))
    endereco_eletronico = Column(String(255))
    representante = Column(String(255))
    cargo_representante = Column(String(100))
    regiao_de_comercializacao = Column(Integer)
    data_registro_ans = Column(Date)
    data_carga = Column(DateTime, default=datetime.utcnow)

class DespesaConsolidada(Base):
    __tablename__ = 'despesas_consolidadas'
    
    id = Column(Integer, primary_key=True, index=True)
    reg_ans = Column(String(20), nullable=False, index=True)
    cd_conta_contabil = Column(String(50), nullable=False, index=True)
    ano = Column(Integer, nullable=False, index=True)
    trimestre = Column(Integer, nullable=False, index=True)
    valor_despesas = Column(Numeric(15, 2), nullable=False)
    data_carga = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        {'schema': 'public'},
    )

class DespesaAgregada(Base):
    __tablename__ = 'despesas_agregadas'
    
    id = Column(Integer, primary_key=True, index=True)
    razao_social = Column(String(255), nullable=False, index=True)
    uf = Column(String(2), nullable=False, index=True)
    total_despesas = Column(Numeric(15, 2), nullable=False)
    media_trimestral = Column(Numeric(15, 2), nullable=False)
    desvio_padrao = Column(Numeric(15, 2))
    coeficiente_variacao = Column(Numeric(10, 2))
    data_carga = Column(DateTime, default=datetime.utcnow)
