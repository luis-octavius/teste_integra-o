"""
ANS Analytics API - Backend FastAPI (Versão Simplificada)
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import distinct, func, text
from sqlalchemy.orm import Session

# Importações locais
from app.api.database import SessionLocal, engine, get_db
from app.api.models import Base, DespesaAgregada, DespesaConsolidada, Operadora
from app.core.config import settings
from app.schemas import (
    DespesaResponse,
    EstatisticaResponse,
    OperadoraDetailResponse,
    OperadoraResponse,
    PaginatedResponse,
)

# Criar tabelas se não existirem
Base.metadata.create_all(bind=engine)


# Lifespan manager simplificado
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting ANS Analytics API...")
    print(f"📊 Database: {settings.DATABASE_URL}")
    print(f"🌐 Environment: {settings.ENVIRONMENT}")

    # Criar cache em memória simples
    app.state.cache = SimpleCache()

    yield

    # Shutdown
    print("👋 Shutting down ANS Analytics API...")


# Inicialização do FastAPI
app = FastAPI(
    title="ANS Analytics API",
    description="API para análise de despesas de operadoras de saúde",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Cache simples em memória
class SimpleCache:
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str):
        """Obtém valor do cache se não expirou"""
        if key in self._cache:
            data, expiry = self._cache[key]
            if datetime.now().timestamp() < expiry:
                return data
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """Define valor no cache com TTL"""
        expiry = datetime.now().timestamp() + ttl_seconds
        self._cache[key] = (value, expiry)

    def clear(self):
        """Limpa cache"""
        self._cache.clear()


# Dependência para cache
def get_cache():
    return app.state.cache if hasattr(app.state, "cache") else SimpleCache()


# ----------------------------
# ROTA 1: GET /api/operadoras
# ----------------------------
@app.get("/api/operadoras", response_model=PaginatedResponse[OperadoraResponse])
async def listar_operadoras(
    page: int = Query(1, ge=1, description="Número da página"),
    limit: int = Query(10, ge=1, le=100, description="Itens por página"),
    razao_social: Optional[str] = Query(None, description="Filtrar por razão social"),
    uf: Optional[str] = Query(None, description="Filtrar por UF"),
    modalidade: Optional[str] = Query(None, description="Filtrar por modalidade"),
    db: Session = Depends(get_db),
):
    """
    Lista todas as operadoras com paginação
    """
    try:
        query = db.query(Operadora)

        # Aplicar filtros
        if razao_social:
            query = query.filter(Operadora.razao_social.ilike(f"%{razao_social}%"))
        if uf:
            query = query.filter(Operadora.uf == uf.upper())
        if modalidade:
            query = query.filter(Operadora.modalidade.ilike(f"%{modalidade}%"))

        # Calcular totais
        total = query.count()

        # Paginação offset-based
        offset = (page - 1) * limit

        # Ordenação padrão
        query = query.order_by(Operadora.razao_social)

        # Aplicar paginação
        operadoras = query.offset(offset).limit(limit).all()

        # Calcular total de páginas
        total_pages = (total + limit - 1) // limit  # Ceil division

        return PaginatedResponse(
            data=operadoras,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar operadoras: {str(e)}",
        )


# ----------------------------
# ROTA 2: GET /api/operadoras/{cnpj}
# ----------------------------
@app.get("/api/operadoras/{cnpj}", response_model=OperadoraDetailResponse)
async def detalhar_operadora(
    cnpj: str, db: Session = Depends(get_db), cache: SimpleCache = Depends(get_cache)
):
    """
    Retorna detalhes de uma operadora específica
    """
    try:
        # Verificar cache primeiro
        cache_key = f"operadora_{cnpj}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Normalizar CNPJ (apenas números)
        cnpj_clean = "".join(filter(str.isdigit, cnpj))

        operadora = db.query(Operadora).filter(Operadora.cnpj == cnpj_clean).first()

        if not operadora:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operadora com CNPJ {cnpj} não encontrada",
            )

        # Armazenar em cache por 5 minutos
        cache.set(cache_key, operadora, ttl_seconds=300)

        return operadora

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar operadora: {str(e)}",
        )


# ----------------------------
# ROTA 3: GET /api/operadoras/{cnpj}/despesas
# ----------------------------
@app.get("/api/operadoras/{cnpj}/despesas", response_model=List[DespesaResponse])
async def historico_despesas(
    cnpj: str,
    ano: Optional[int] = Query(None, description="Filtrar por ano"),
    trimestre: Optional[int] = Query(
        None, ge=1, le=4, description="Filtrar por trimestre"
    ),
    db: Session = Depends(get_db),
):
    """
    Retorna histórico de despesas da operadora
    """
    try:
        # Buscar operadora primeiro para obter registro_ans
        cnpj_clean = "".join(filter(str.isdigit, cnpj))
        operadora = db.query(Operadora).filter(Operadora.cnpj == cnpj_clean).first()

        if not operadora:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operadora com CNPJ {cnpj} não encontrada",
            )

        # Buscar despesas consolidadas
        query = db.query(DespesaConsolidada).filter(
            DespesaConsolidada.reg_ans == operadora.registro_operadora
        )

        if ano:
            query = query.filter(DespesaConsolidada.ano == ano)
        if trimestre:
            query = query.filter(DespesaConsolidada.trimestre == trimestre)

        # Ordenar por ano e trimestre
        despesas = query.order_by(
            DespesaConsolidada.ano.desc(), DespesaConsolidada.trimestre.desc()
        ).all()

        return despesas

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar despesas: {str(e)}",
        )


# ----------------------------
# ROTA 4: GET /api/estatisticas
# ----------------------------
@app.get("/api/estatisticas", response_model=EstatisticaResponse)
async def estatisticas_gerais(
    db: Session = Depends(get_db), cache: SimpleCache = Depends(get_cache)
):
    """
    Retorna estatísticas agregadas
    """
    try:
        # Verificar cache (10 minutos)
        cache_key = "estatisticas_gerais"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # Calcular estatísticas
        total_operadoras = db.query(Operadora).count()

        # Top 5 operadoras por despesa
        top_operadoras = (
            db.query(DespesaAgregada)
            .order_by(DespesaAgregada.total_despesas.desc())
            .limit(5)
            .all()
        )

        # Distribuição por UF
        distribuicao_uf = (
            db.query(
                DespesaAgregada.uf,
                func.sum(DespesaAgregada.total_despesas).label("total"),
            )
            .group_by(DespesaAgregada.uf)
            .order_by(text("total DESC"))
            .all()
        )

        # Totais gerais
        resultado = db.query(
            func.sum(DespesaAgregada.total_despesas).label("total_despesas"),
            func.avg(DespesaAgregada.total_despesas).label("media_despesas"),
            func.count(distinct(DespesaAgregada.razao_social)).label(
                "total_operadoras_ativas"
            ),
        ).first()

        estatisticas = EstatisticaResponse(
            total_despesas=resultado.total_despesas or 0,
            media_despesas=resultado.media_despesas or 0,
            total_operadoras=total_operadoras,
            total_operadoras_ativas=resultado.total_operadoras_ativas or 0,
            top_operadoras=top_operadoras,
            distribuicao_uf=[
                {"uf": item.uf, "total": item.total} for item in distribuicao_uf
            ],
            atualizado_em=datetime.now(),
        )

        # Armazenar em cache por 10 minutos
        cache.set(cache_key, estatisticas, ttl_seconds=600)

        return estatisticas

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao calcular estatísticas: {str(e)}",
        )


# ----------------------------
# ROTA ADICIONAL: Busca
# ----------------------------
@app.get("/api/buscar")
async def buscar_operadoras(
    q: str = Query(..., min_length=2, description="Termo de busca"),
    db: Session = Depends(get_db),
):
    """
    Busca avançada em operadoras
    """
    try:
        termo = f"%{q}%"

        resultados = (
            db.query(Operadora)
            .filter(
                db.or_(
                    Operadora.razao_social.ilike(termo),
                    Operadora.cnpj.ilike(termo),
                    Operadora.nome_fantasia.ilike(termo),
                    Operadora.cidade.ilike(termo),
                )
            )
            .limit(20)
            .all()
        )

        return resultados

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na busca: {str(e)}",
        )


# ----------------------------
# Health check
# ----------------------------
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check da API e banco de dados
    """
    try:
        # Testar conexão com banco
        db.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "ans-analytics-api",
            "database": "connected",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}",
        )


# ----------------------------
# Tratamento de erros
# ----------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "path": request.url.path,
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "message": "Erro interno do servidor",
            "path": request.url.path,
            "timestamp": datetime.now().isoformat(),
        },
    )


# ----------------------------
# Ponto de entrada
# ----------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
