"""Repository do contrato Produto x Fornecedor (R-ARQ-01)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.produto_fornecedor import ProdutoFornecedor


def get_by_id(db: Session, pf_id: int) -> ProdutoFornecedor | None:
    """Retorna o contrato pelo id, ou None se nao existir."""
    return db.get(ProdutoFornecedor, pf_id)


def list_by_produto(db: Session, produto_id: int) -> list[ProdutoFornecedor]:
    """Lista todos os contratos vinculados a um produto."""
    stmt = select(ProdutoFornecedor).where(
        ProdutoFornecedor.produto_id == produto_id
    )
    return list(db.execute(stmt).scalars().all())


def list_all(db: Session) -> list[ProdutoFornecedor]:
    """Retorna todos os contratos sem filtro nem ordenacao no banco.

    Filtros/ordenacao sao feitos em memoria pelos services (R-ALG-01/02).
    """
    stmt = select(ProdutoFornecedor)
    return list(db.execute(stmt).scalars().all())


def get_by_produto_e_fornecedor(
    db: Session, produto_id: int, fornecedor_id: int
) -> ProdutoFornecedor | None:
    """Verifica se um contrato (produto, fornecedor) existe."""
    stmt = select(ProdutoFornecedor).where(
        ProdutoFornecedor.produto_id == produto_id,
        ProdutoFornecedor.fornecedor_id == fornecedor_id,
    )
    return db.execute(stmt).scalar_one_or_none()
