"""Catalogo de tools de Usuario (PRD §11.3).

Mesma estrutura de tools_admin: por tool, uma classe Pydantic *Args e um
dict DECL_* no formato function declaration do Gemini. Os agregados
TOOLS_USUARIO e SCHEMAS_ARGS_USUARIO sao o que Stephanie passa ao SDK e usa
para validar o retorno do modelo (PRD §11.4 passo 2).
"""
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


# --- buscar_produtos ---


class BuscarProdutosArgs(BaseModel):
    """Argumentos da tool buscar_produtos.

    Ambos opcionais: o service do backend (R-ALG-01) decide se aplica
    filtro por nome, categoria, ou lista tudo. Nao impomos "pelo menos um"
    porque o modelo pode legitimamente pedir um catalogo completo.
    """

    termo: str | None = Field(default=None, max_length=120)
    categoria: str | None = Field(default=None, max_length=60)


DECL_BUSCAR_PRODUTOS: dict[str, Any] = {
    "name": "buscar_produtos",
    "description": (
        "Busca produtos no catalogo por nome (termo) e/ou categoria. "
        "Ambos os filtros sao opcionais. Apenas Usuario pode chamar."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "termo": {
                "type": "string",
                "description": "Texto a buscar no nome do produto (opcional).",
            },
            "categoria": {
                "type": "string",
                "description": "Categoria a filtrar (opcional).",
            },
        },
    },
}


# --- cadastrar_produto ---
#
# GAP a sinalizar para o backend: PRD §11.3 pede apenas 5 argumentos, mas
# ProdutoFornecedor tem prazo_entrega_dias NOT NULL. O service do backend
# precisa decidir entre (a) atribuir um default no momento da criacao do
# ProdutoFornecedor (ex.: 7 dias) ou (b) expor um tool dedicado para o
# usuario ajustar prazo depois. A camada NLU segue o catalogo literal.


class CadastrarProdutoArgs(BaseModel):
    """Argumentos da tool cadastrar_produto (RN-02)."""

    nome: str = Field(min_length=1, max_length=120)
    categoria: str = Field(min_length=1, max_length=60)
    fornecedor_id: int = Field(gt=0)
    preco_contratado: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    qtd_minima_pedido: int = Field(gt=0)


DECL_CADASTRAR_PRODUTO: dict[str, Any] = {
    "name": "cadastrar_produto",
    "description": (
        "Cria um produto no catalogo e o vincula a um fornecedor (RN-02). "
        "Apenas Usuario pode chamar."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "nome": {"type": "string", "description": "Nome do produto."},
            "categoria": {
                "type": "string",
                "description": "Categoria do produto.",
            },
            "fornecedor_id": {
                "type": "integer",
                "description": "ID do fornecedor a vincular.",
            },
            "preco_contratado": {
                "type": "number",
                "description": "Preco unitario no contrato com o fornecedor.",
            },
            "qtd_minima_pedido": {
                "type": "integer",
                "description": (
                    "Quantidade minima por pedido junto a esse fornecedor."
                ),
            },
        },
        # `required` ausente: o frontend abre formulario com dropdown de
        # fornecedor; CadastrarProdutoArgs valida obrigatoriedade no submit.
    },
}


# --- consultar_estoque ---


class ConsultarEstoqueArgs(BaseModel):
    """Argumentos da tool consultar_estoque (sem slots, PRD §11.3)."""

    # Sem campos. Mantemos a classe para que SCHEMAS_ARGS_USUARIO permaneca
    # consistente (todo tool tem uma classe de args correspondente).


DECL_CONSULTAR_ESTOQUE: dict[str, Any] = {
    "name": "consultar_estoque",
    "description": (
        "Consulta o estoque do proprio usuario com semaforo Kanban (RN-06). "
        "Apenas Usuario pode chamar."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}


# --- configurar_pontos_reposicao ---


class ConfigurarPontosReposicaoArgs(BaseModel):
    """Argumentos da tool configurar_pontos_reposicao (RN-06)."""

    produto_id: int = Field(gt=0)
    ponto_reposicao: int = Field(ge=0)
    ponto_amarelo: int = Field(gt=0)

    @model_validator(mode="after")
    def _validar_faixas_semaforo(self) -> "ConfigurarPontosReposicaoArgs":
        # RN-06: ponto_amarelo > ponto_reposicao para a faixa "Amarelo" existir.
        if self.ponto_amarelo <= self.ponto_reposicao:
            raise ValueError(
                "ponto_amarelo deve ser maior que ponto_reposicao (RN-06)."
            )
        return self


DECL_CONFIGURAR_PONTOS_REPOSICAO: dict[str, Any] = {
    "name": "configurar_pontos_reposicao",
    "description": (
        "Define as faixas do semaforo Kanban (RN-06) para um produto. "
        "ponto_amarelo deve ser maior que ponto_reposicao. Apenas Usuario."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "produto_id": {"type": "integer"},
            "ponto_reposicao": {
                "type": "integer",
                "description": "Limite que dispara faixa Vermelho.",
            },
            "ponto_amarelo": {
                "type": "integer",
                "description": "Limite Amarelo (deve ser maior que ponto_reposicao).",
            },
        },
        # `required` ausente: ConfigurarPontosReposicaoArgs valida no submit
        # do formulario (incl. a regra ponto_amarelo > ponto_reposicao).
    },
}


# --- criar_pedido_manual ---


class ItemPedidoManual(BaseModel):
    """Linha de um pedido manual."""

    produto_fornecedor_id: int = Field(gt=0)
    quantidade: int = Field(gt=0)


class CriarPedidoManualArgs(BaseModel):
    """Argumentos da tool criar_pedido_manual."""

    # Lista nao pode ser vazia: pedido sem item nao faz sentido.
    itens: list[ItemPedidoManual] = Field(min_length=1)


DECL_CRIAR_PEDIDO_MANUAL: dict[str, Any] = {
    "name": "criar_pedido_manual",
    "description": (
        "Cria um pedido manual com varios itens. Cada item referencia um "
        "contrato Produto-Fornecedor (RN-02). Apenas Usuario."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "itens": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "produto_fornecedor_id": {"type": "integer"},
                        "quantidade": {"type": "integer"},
                    },
                    "required": ["produto_fornecedor_id", "quantidade"],
                },
                "description": "Lista nao vazia de itens do pedido.",
            },
        },
        # `required` ausente: o frontend abre formulario com lista dinamica
        # de itens (dropdown produto-fornecedor + qtd). Validacao por CriarPedidoManualArgs.
    },
}


# --- pedido_reposicao ---


class PedidoReposicaoArgs(BaseModel):
    """Argumentos da tool pedido_reposicao (RN-07)."""

    produto_id: int = Field(gt=0)


DECL_PEDIDO_REPOSICAO: dict[str, Any] = {
    "name": "pedido_reposicao",
    "description": (
        "Solicita pedido automatico de reposicao para um produto. So pode "
        "ser chamada se o item estiver em Amarelo ou Vermelho (RN-07); o "
        "backend valida. Apenas Usuario."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "produto_id": {
                "type": "integer",
                "description": "ID do produto a repor.",
            },
        },
        # `required` ausente: dropdown do estoque no formulario; validacao
        # de obrigatoriedade via PedidoReposicaoArgs.
    },
}


# --- listar_pedidos ---


TipoOrigemPedido = Literal["manual", "automatico"]
_ORIGENS_VALIDAS = ["manual", "automatico"]


class ListarPedidosArgs(BaseModel):
    """Argumentos da tool listar_pedidos."""

    filtro: TipoOrigemPedido | None = None


DECL_LISTAR_PEDIDOS: dict[str, Any] = {
    "name": "listar_pedidos",
    "description": (
        "Lista pedidos do proprio usuario. Opcionalmente filtra por origem. "
        "Apenas Usuario pode chamar."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "filtro": {
                "type": "string",
                "enum": _ORIGENS_VALIDAS,
                "description": "Origem do pedido para filtrar (opcional).",
            },
        },
    },
}


# Catalogo agregado, na ordem do PRD §11.3.
TOOLS_USUARIO: list[dict[str, Any]] = [
    DECL_BUSCAR_PRODUTOS,
    DECL_CADASTRAR_PRODUTO,
    DECL_CONSULTAR_ESTOQUE,
    DECL_CONFIGURAR_PONTOS_REPOSICAO,
    DECL_CRIAR_PEDIDO_MANUAL,
    DECL_PEDIDO_REPOSICAO,
    DECL_LISTAR_PEDIDOS,
]

SCHEMAS_ARGS_USUARIO: dict[str, type[BaseModel]] = {
    "buscar_produtos": BuscarProdutosArgs,
    "cadastrar_produto": CadastrarProdutoArgs,
    "consultar_estoque": ConsultarEstoqueArgs,
    "configurar_pontos_reposicao": ConfigurarPontosReposicaoArgs,
    "criar_pedido_manual": CriarPedidoManualArgs,
    "pedido_reposicao": PedidoReposicaoArgs,
    "listar_pedidos": ListarPedidosArgs,
}
