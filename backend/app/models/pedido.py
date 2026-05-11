"""Models PedidoCompra e ItemPedido (PRD §8).

PedidoCompra é o cabeçalho do pedido (quem, status, origem, quando).
ItemPedido referencia o contrato específico ProdutoFornecedor (RN-02)
para rastrear qual fornecedor atendeu cada item.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    DateTime,
    Enum as SqlEnum,
    ForeignKey,
    Integer,
    Numeric,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StatusPedido(str, Enum):
    """Estados do ciclo de vida de um PedidoCompra (PRD §8)."""

    PENDENTE = "pendente"
    CONFIRMADO = "confirmado"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


class OrigemPedido(str, Enum):
    """Como o pedido foi criado: manual pelo usuário ou automático (RN-07)."""

    MANUAL = "manual"
    AUTOMATICO = "automatico"


class PedidoCompra(Base):
    """Tabela 'pedidos_compra' - cabeçalho do pedido."""

    __tablename__ = "pedidos_compra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Enum como VARCHAR (mesmo padrão de UserRole) — compatível com SQLite.
    status: Mapped[StatusPedido] = mapped_column(
        SqlEnum(
            StatusPedido,
            native_enum=False,
            length=20,
            create_constraint=True,
            name="status_pedido",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )
    origem: Mapped[OrigemPedido] = mapped_column(
        SqlEnum(
            OrigemPedido,
            native_enum=False,
            length=20,
            create_constraint=True,
            name="origem_pedido",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )
    # Timestamp do servidor evita drift entre clock do app e do banco e
    # garante imutabilidade da hora original mesmo em reimport.
    criado_em: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class ItemPedido(Base):
    """Tabela 'itens_pedido' - linha de pedido com contrato específico."""

    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(
        ForeignKey("pedidos_compra.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Referencia o contrato específico (Produto + Fornecedor) para rastrear
    # qual fornecedor atendeu este item (RN-02).
    produto_fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("produtos_fornecedores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False)
    # Snapshot do preço no momento do pedido. Numeric(10, 2) casa com
    # ProdutoFornecedor.preco_contratado.
    preco_unitario: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
