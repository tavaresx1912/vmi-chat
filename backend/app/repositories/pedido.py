"""Repository do PedidoCompra e ItemPedido (R-ARQ-01)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pedido import ItemPedido, PedidoCompra
from app.models.produto_fornecedor import ProdutoFornecedor
from app.models.user import User


def get_by_id(db: Session, pedido_id: int) -> PedidoCompra | None:
    """Retorna o pedido pelo id, ou None se nao existir."""
    return db.get(PedidoCompra, pedido_id)


def list_by_user(db: Session, usuario_id: int) -> list[PedidoCompra]:
    """Lista todos os pedidos de um usuario."""
    stmt = select(PedidoCompra).where(PedidoCompra.usuario_id == usuario_id)
    return list(db.execute(stmt).scalars().all())


def list_itens_by_pedido(db: Session, pedido_id: int) -> list[ItemPedido]:
    """Lista os itens de um pedido."""
    stmt = select(ItemPedido).where(ItemPedido.pedido_id == pedido_id)
    return list(db.execute(stmt).scalars().all())


def list_clientes_do_fornecedor(
    db: Session, fornecedor_id: int
) -> list[User]:
    """Usuarios distintos que pediram produtos deste fornecedor.

    Query relacional (JOIN + WHERE + DISTINCT) — nao se aplica a regra
    R-ALG-01, que trata de "localizar elementos em colecoes" no codigo da
    aplicacao, nao de operacoes algebricas no banco.
    """
    stmt = (
        select(User)
        .join(PedidoCompra, PedidoCompra.usuario_id == User.id)
        .join(ItemPedido, ItemPedido.pedido_id == PedidoCompra.id)
        .join(
            ProdutoFornecedor,
            ProdutoFornecedor.id == ItemPedido.produto_fornecedor_id,
        )
        .where(ProdutoFornecedor.fornecedor_id == fornecedor_id)
        .distinct()
    )
    return list(db.execute(stmt).scalars().all())


def fornecedor_tem_itens_no_pedido(
    db: Session, fornecedor_id: int, pedido_id: int
) -> bool:
    """Pedido contem ao menos um item suprido por este fornecedor?"""
    stmt = (
        select(ItemPedido.id)
        .join(
            ProdutoFornecedor,
            ProdutoFornecedor.id == ItemPedido.produto_fornecedor_id,
        )
        .where(
            ItemPedido.pedido_id == pedido_id,
            ProdutoFornecedor.fornecedor_id == fornecedor_id,
        )
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none() is not None
