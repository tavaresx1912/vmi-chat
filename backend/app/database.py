"""Configuração do SQLAlchemy: engine, sessão e classe base dos models.

Esta camada é puramente de infraestrutura. Não contém regras de negócio
(R-ARQ-01) — quem usa estas peças é a camada de Repositories.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# O argumento check_same_thread=False só é necessário para SQLite, porque
# por padrão ele não permite que a mesma conexão seja usada por múltiplas
# threads. Em PostgreSQL este argumento não se aplica.
connect_args: dict = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(settings.database_url, connect_args=connect_args)

# Fábrica de sessões. Cada requisição HTTP abre e fecha a sua própria sessão.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Classe base para todos os models SQLAlchemy do projeto."""


def get_db():
    """Dependência do FastAPI que entrega uma sessão do banco por requisição.

    Garante que a sessão seja sempre fechada ao final, mesmo em caso de erro.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
