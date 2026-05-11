"""Schemas Pydantic de entrada e saída para o Produto."""
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProdutoCreate(BaseModel):
    """Dados básicos para criar um produto isolado (sem vínculo)."""

    nome: str = Field(min_length=1, max_length=120)
    descricao: str | None = Field(default=None, max_length=500)
    categoria: str = Field(min_length=1, max_length=60)


class ProdutoRead(BaseModel):
    """Resposta pública de um produto."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None
    categoria: str


class CadastrarProdutoInput(BaseModel):
    """Input do endpoint POST /usuario/produtos (RN-02).

    Cria um Produto novo e o vincula a um Fornecedor existente numa
    única transação. `descricao` é opcional; `prazo_entrega_dias` usa
    default no service (gap apontado pela Ingrid: PRD §11.3 não expõe
    prazo no tool, mas o model exige).
    """

    nome: str = Field(min_length=1, max_length=120)
    categoria: str = Field(min_length=1, max_length=60)
    descricao: str | None = Field(default=None, max_length=500)
    fornecedor_id: int = Field(gt=0)
    preco_contratado: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    qtd_minima_pedido: int = Field(gt=0)
