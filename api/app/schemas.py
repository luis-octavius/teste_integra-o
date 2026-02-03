"""
Schemas Pydantic para validação e serialização
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Generic, TypeVar
from datetime import date, datetime
from decimal import Decimal

T = TypeVar('T')

# Schemas base
class OperadoraBase(BaseModel):
    registro_operadora: str
    cnpj: str
    razao_social: str
    nome_fantasia: Optional[str] = None
    modalidade: Optional[str] = None
    uf: str
    cidade: Optional[str] = None
    data_registro_ans: Optional[date] = None

class OperadoraResponse(OperadoraBase):
    id: int
    
    model_config = {"from_attributes": True}

class OperadoraDetailResponse(OperadoraResponse):
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cep: Optional[str] = None
    ddd: Optional[str] = None
    telefone: Optional[str] = None
    fax: Optional[str] = None
    endereco_eletronico: Optional[str] = None
    representante: Optional[str] = None
    cargo_representante: Optional[str] = None
    regiao_de_comercializacao: Optional[int] = None

class DespesaBase(BaseModel):
    reg_ans: str
    cd_conta_contabil: str
    ano: int
    trimestre: int
    valor_despesas: Decimal

class DespesaResponse(DespesaBase):
    id: int
    
    model_config = {"from_attributes": True}

class DespesaAgregadaResponse(BaseModel):
    razao_social: str
    uf: str
    total_despesas: Decimal
    media_trimestral: Decimal
    coeficiente_variacao: Optional[Decimal] = None
    
    model_config = {"from_attributes": True}

class DistribuicaoUF(BaseModel):
    uf: str
    total: Decimal

class EstatisticaResponse(BaseModel):
    total_despesas: Decimal
    media_despesas: Decimal
    total_operadoras: int
    total_operadoras_ativas: int
    top_operadoras: List[DespesaAgregadaResponse]
    distribuicao_uf: List[DistribuicaoUF]
    atualizado_em: datetime

# Schema para paginação
class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool
