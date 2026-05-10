"""Schemas Pydantic de entrada e saída para o Fornecedor."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class FornecedorCreate(BaseModel):
    """Dados para criar um fornecedor.

    Conforme PRD seção 5.1, o Admin informa nome, e-mail, senha e CNPJ;
    a camada de service criará o User (com role='fornecedor') e o
    Fornecedor em uma única transação.
    """

    nome: str = Field(min_length=1, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=6, max_length=128)
    # CNPJ apenas com dígitos, sem máscara. A formatação visual fica no frontend.
    cnpj: str = Field(min_length=14, max_length=14, pattern=r"^\d{14}$")


class FornecedorRead(BaseModel):
    """Resposta pública de um fornecedor."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    nome: str
    cnpj: str
