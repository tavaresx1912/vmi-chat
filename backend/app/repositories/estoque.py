"""Repository do Estoque por (Produto, Usuario) (R-ARQ-01)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.estoque import Estoque


def get_by_produto_e_user(
    db: Session, produto_id: int, usuario_id: int
) -> Estoque | None:
    """Retorna o registro de estoque para (produto, usuario), ou None."""
    stmt = select(Estoque).where(
        Estoque.produto_id == produto_id,
        Estoque.usuario_id == usuario_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def list_by_user(db: Session, usuario_id: int) -> list[Estoque]:
    """Lista todos os registros de estoque do usuario."""
    stmt = select(Estoque).where(Estoque.usuario_id == usuario_id)
    return list(db.execute(stmt).scalars().all())
