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
