"""Catalogo de tools de Fornecedor (PRD §11.3, RN-03 - VMI).

Mesma estrutura de tools_admin e tools_usuario: para cada tool, uma classe
Pydantic *Args e um dict DECL_* no formato function declaration do Gemini.
Os agregados TOOLS_FORNECEDOR e SCHEMAS_ARGS_FORNECEDOR sao o que Stephanie
passa ao SDK e usa para validar o retorno do modelo.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field


# Status do pedido, espelhado de StatusPedido no backend (PRD §8) sem
# import direto para preservar a independencia da camada NLU.
TipoStatusPedido = Literal[
    "pendente", "confirmado", "enviado", "entregue", "cancelado"
]
_STATUS_VALIDOS = ["pendente", "confirmado", "enviado", "entregue", "cancelado"]


# --- atualizar_estoque ---


class AtualizarEstoqueArgs(BaseModel):
    """Argumentos da tool atualizar_estoque (RN-03 - gestao VMI)."""

    produto_id: int = Field(gt=0)
    # Quantidade absoluta apos a atualizacao (nao e delta). Zero e valido:
    # o fornecedor pode zerar um estoque, mas nao informar valor negativo.
    nova_quantidade: int = Field(ge=0)


DECL_ATUALIZAR_ESTOQUE: dict[str, Any] = {
    "name": "atualizar_estoque",
    "description": (
        "Atualiza a quantidade em estoque de um produto (VMI - RN-03). "
        "Apenas Fornecedor pode chamar."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "produto_id": {
                "type": "integer",
                "description": "ID do produto a atualizar.",
            },
            "nova_quantidade": {
                "type": "integer",
                "description": "Nova quantidade absoluta em estoque (>= 0).",
            },
        },
        "required": ["produto_id", "nova_quantidade"],
    },
}


# --- atualizar_status_pedido ---


class AtualizarStatusPedidoArgs(BaseModel):
    """Argumentos da tool atualizar_status_pedido."""

    pedido_id: int = Field(gt=0)
    novo_status: TipoStatusPedido


DECL_ATUALIZAR_STATUS_PEDIDO: dict[str, Any] = {
    "name": "atualizar_status_pedido",
    "description": (
        "Atualiza o status de um pedido. Apenas Fornecedor pode chamar. "
        "O backend valida transicoes invalidas de status."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "pedido_id": {
                "type": "integer",
                "description": "ID do pedido a atualizar.",
            },
            "novo_status": {
                "type": "string",
                "enum": _STATUS_VALIDOS,
                "description": "Novo status do pedido.",
            },
        },
        "required": ["pedido_id", "novo_status"],
    },
}


# Catalogo agregado, na ordem do PRD §11.3.
TOOLS_FORNECEDOR: list[dict[str, Any]] = [
    DECL_ATUALIZAR_ESTOQUE,
    DECL_ATUALIZAR_STATUS_PEDIDO,
]

SCHEMAS_ARGS_FORNECEDOR: dict[str, type[BaseModel]] = {
    "atualizar_estoque": AtualizarEstoqueArgs,
    "atualizar_status_pedido": AtualizarStatusPedidoArgs,
}
