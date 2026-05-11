"""Schemas Pydantic de entrada e saída para o Produto."""
from pydantic import BaseModel, ConfigDict, Field


class ProdutoCreate(BaseModel):
    """Dados para cadastrar um produto no catálogo (intent `cadastrar_produto`)."""

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
