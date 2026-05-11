"""Schemas Pydantic de entrada e saída para o contrato Produto x Fornecedor."""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProdutoFornecedorCreate(BaseModel):
    """Dados para registrar um contrato Produto x Fornecedor (RN-02)."""

    produto_id: int = Field(gt=0)
    fornecedor_id: int = Field(gt=0)
    preferencial: bool = False
    # max_digits/decimal_places casam com a coluna Numeric(10, 2) do model.
    preco_contratado: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    prazo_entrega_dias: int = Field(gt=0)
    qtd_minima_pedido: int = Field(gt=0)


class ProdutoFornecedorRead(BaseModel):
    """Resposta pública de um contrato Produto x Fornecedor."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    fornecedor_id: int
    preferencial: bool
    preco_contratado: Decimal
    prazo_entrega_dias: int
    qtd_minima_pedido: int
