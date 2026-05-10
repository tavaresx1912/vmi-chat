"""Ponto de entrada da API VMI Chat.

Cria a aplicação FastAPI e registra os routers. As rotas em si vivem em
`app/routes/` — este arquivo só compõe a aplicação.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine

# Estes imports parecem "não usados", mas são necessários: eles registram
# os models em Base.metadata, sem o que create_all não criaria as tabelas.
from app.models import fornecedor, user  # noqa: F401
from app.routes import auth, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Cria as tabelas no banco quando a aplicação sobe.

    Em produção isto seria substituído por migrações com Alembic. Aqui
    usamos create_all por simplicidade, conforme R-COD-04.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="VMI Chat API",
    version="0.1.0",
    description="API do sistema de Vendor Managed Inventory.",
    lifespan=lifespan,
)

# Registramos cada router separadamente para manter a composição explícita.
app.include_router(health.router)
app.include_router(auth.router)
