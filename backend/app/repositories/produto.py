"""Repository do Produto: acesso direto a tabela 'produtos' (R-ARQ-01)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.produto import Produto


def get_by_id(db: Session, produto_id: int) -> Produto | None:
    """Retorna o produto pelo id, ou None se nao existir."""
    return db.get(Produto, produto_id)


def list_all(db: Session) -> list[Produto]:
    """Retorna todos os produtos sem filtro/ordenacao no banco.

    Filtros e ordenacao sao aplicados em memoria pelos services
    (R-ALG-01/02).
    """
    stmt = select(Produto)
    return list(db.execute(stmt).scalars().all())
