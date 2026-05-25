"""Repository do Fornecedor: acesso direto a tabela 'fornecedores'.

Sem regra de negocio (R-ARQ-01). Para listar com busca/ordenacao usa-se
list_all() e os algoritmos manuais em services/busca_ordenacao.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fornecedor import Fornecedor


def get_by_id(db: Session, fornecedor_id: int) -> Fornecedor | None:
    """Retorna o fornecedor pelo id, ou None se nao existir."""
    return db.get(Fornecedor, fornecedor_id)


def get_by_cnpj(db: Session, cnpj: str) -> Fornecedor | None:
    """Retorna o fornecedor pelo CNPJ, ou None se nao existir."""
    stmt = select(Fornecedor).where(Fornecedor.cnpj == cnpj)
    return db.execute(stmt).scalar_one_or_none()


def list_all(db: Session) -> list[Fornecedor]:
    """Retorna todos os fornecedores sem filtro nem ordenacao no banco.

    Filtros/ordenacao sao feitos em memoria pelos services (R-ALG-01/02).
    """
    stmt = select(Fornecedor)
    return list(db.execute(stmt).scalars().all())
