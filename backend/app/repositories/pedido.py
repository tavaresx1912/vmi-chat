"""Repository do PedidoCompra e ItemPedido (R-ARQ-01)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pedido import ItemPedido, PedidoCompra


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
