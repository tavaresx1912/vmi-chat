"""Schemas Pydantic de entrada e saída para PedidoCompra e ItemPedido."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.pedido import OrigemPedido, StatusPedido


class PedidoCompraCreate(BaseModel):
    """Dados para criar um cabeçalho de pedido.

    O status inicial é definido pela camada de service (transição controlada
    do fluxo) e não vem do cliente.
    """

    usuario_id: int = Field(gt=0)
    origem: OrigemPedido


class PedidoCompraRead(BaseModel):
    """Resposta pública de um PedidoCompra."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    status: StatusPedido
    origem: OrigemPedido
    criado_em: datetime


class ItemPedidoCreate(BaseModel):
    """Dados para incluir um item num pedido.

    preco_unitario não é informado pelo cliente — vem como snapshot de
    ProdutoFornecedor.preco_contratado no momento da criação.
    """

    pedido_id: int = Field(gt=0)
    produto_fornecedor_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)


class ItemPedidoRead(BaseModel):
    """Resposta pública de um ItemPedido."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    pedido_id: int
    produto_fornecedor_id: int
    quantidade: int
    preco_unitario: Decimal


class ItemPedidoInput(BaseModel):
    """Linha de input de um pedido manual (sem pedido_id, sem preço).

    O `pedido_id` é atribuído pelo service no momento da criação. O
    `preco_unitario` vem como snapshot do `ProdutoFornecedor.preco_contratado`.
    """

    produto_fornecedor_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)


class PedidoCompraComItensCreate(BaseModel):
    """Payload composto para criar um pedido manual com seus itens."""

    itens: list[ItemPedidoInput] = Field(min_length=1)


class PedidoCompraComItensRead(PedidoCompraRead):
    """Resposta enriquecida: cabeçalho do pedido + itens detalhados."""

    itens: list[ItemPedidoRead]
