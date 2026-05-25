"""Schemas Pydantic de entrada e saída para o Fornecedor."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.pedido import StatusPedido


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


class FornecedorSimilarRead(BaseModel):
    """Fornecedor descoberto via BFS no grafo de similaridade.

    `distancia` é o número de hops desde a origem da busca (1 = vizinho
    direto); `peso_aresta_descobridor` é a quantidade de produtos em
    comum com quem o descobriu na travessia.
    """

    id: int
    nome: str
    cnpj: str
    distancia: int = Field(ge=1)
    peso_aresta_descobridor: int = Field(ge=1)


class AtualizarEstoqueInput(BaseModel):
    """Input do PATCH /fornecedor/estoque (VMI - RN-03)."""

    produto_id: int = Field(gt=0)
    usuario_id: int = Field(gt=0)
    nova_quantidade: int = Field(ge=0)


class AtualizarStatusPedidoInput(BaseModel):
    """Input do PATCH /fornecedor/pedidos/{pedido_id}/status."""

    novo_status: StatusPedido
