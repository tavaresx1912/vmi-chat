"""Texto-resumo de acoes (C5, RNF-13).

Stephanie consome este modulo para montar o cartao de confirmacao antes
de chamar a API: para cada tool de ESCRITA, devolve uma sentenca em 1a
pessoa explicando o que o sistema vai fazer ("Vou X. Confirma?").

Tools de leitura nao precisam de confirmacao (RNF-13 cobre apenas
escritas); chamar `gerar_resumo_acao` com uma tool de leitura levanta
`ToolSomenteLeituraError` — o caller filtra antes.
"""
from decimal import Decimal
from typing import Any, Callable


class ToolDesconhecidaError(Exception):
    """Nome de tool sem handler de resumo registrado."""


class ToolSomenteLeituraError(Exception):
    """Tool de leitura nao tem cartao de confirmacao (RNF-13)."""


# Tools de leitura listadas explicitamente para distinguir de "desconhecida".
_LEITURAS: frozenset[str] = frozenset(
    {
        "listar_usuarios",
        "buscar_produtos",
        "consultar_estoque",
        "listar_pedidos",
    }
)


def _fmt_preco(valor: Any) -> str:
    """Formata preco no padrao BR: 'R$ 2,50'. Aceita Decimal/str/float/int."""
    d = Decimal(str(valor))
    inteiro, _, dec = f"{d:.2f}".partition(".")
    return f"R$ {inteiro},{dec}"


# --- Handlers por tool de escrita ---


def _resumo_criar_usuario(a: dict[str, Any]) -> str:
    return (
        f"Vou criar o usuário **{a['nome']}** ({a['email']}) "
        f"com papel **{a['role']}**. Confirma?"
    )


def _resumo_desativar_usuario(a: dict[str, Any]) -> str:
    return f"Vou desativar o usuário **#{a['usuario_id']}**. Confirma?"


def _resumo_cadastrar_produto(a: dict[str, Any]) -> str:
    return (
        f"Vou cadastrar o produto **{a['nome']}** "
        f"(categoria: {a['categoria']}) vinculado ao fornecedor "
        f"**#{a['fornecedor_id']}**, preço **{_fmt_preco(a['preco_contratado'])}** "
        f"e mínimo **{a['qtd_minima_pedido']}**. Confirma?"
    )


def _resumo_configurar_pontos(a: dict[str, Any]) -> str:
    return (
        f"Vou configurar os pontos do produto **#{a['produto_id']}** "
        f"como reposição **{a['ponto_reposicao']}** e amarelo "
        f"**{a['ponto_amarelo']}**. Confirma?"
    )


def _resumo_criar_pedido_manual(a: dict[str, Any]) -> str:
    itens = a.get("itens") or []
    if not itens:
        return "Vou criar um pedido **vazio**. Confirma?"
    partes: list[str] = []
    for it in itens:
        partes.append(
            f"{it['quantidade']}x contrato #{it['produto_fornecedor_id']}"
        )
    sumario = ", ".join(partes)
    return (
        f"Vou criar um pedido com **{len(itens)} itens**: {sumario}. Confirma?"
    )


def _resumo_pedido_reposicao(a: dict[str, Any]) -> str:
    return (
        f"Vou solicitar reposição do produto **#{a['produto_id']}**. Confirma?"
    )


def _resumo_atualizar_estoque(a: dict[str, Any]) -> str:
    return (
        f"Vou atualizar o estoque do produto **#{a['produto_id']}** "
        f"do cliente **#{a['usuario_id']}** para "
        f"**{a['nova_quantidade']} unidades**. Confirma?"
    )


def _resumo_atualizar_status_pedido(a: dict[str, Any]) -> str:
    return (
        f"Vou marcar o pedido **#{a['pedido_id']}** como "
        f"**{a['novo_status']}**. Confirma?"
    )


_HANDLERS: dict[str, Callable[[dict[str, Any]], str]] = {
    "criar_usuario": _resumo_criar_usuario,
    "desativar_usuario": _resumo_desativar_usuario,
    "cadastrar_produto": _resumo_cadastrar_produto,
    "configurar_pontos_reposicao": _resumo_configurar_pontos,
    "criar_pedido_manual": _resumo_criar_pedido_manual,
    "pedido_reposicao": _resumo_pedido_reposicao,
    "atualizar_estoque": _resumo_atualizar_estoque,
    "atualizar_status_pedido": _resumo_atualizar_status_pedido,
}


def gerar_resumo_acao(tool_name: str, args: dict[str, Any]) -> str:
    """Devolve texto-resumo de uma tool de escrita (1a pessoa, "Confirma?").

    Levanta ToolSomenteLeituraError em tools de leitura (sem confirmacao
    por RNF-13) e ToolDesconhecidaError se o nome nao esta no catalogo.
    """
    if tool_name in _LEITURAS:
        raise ToolSomenteLeituraError(tool_name)
    handler = _HANDLERS.get(tool_name)
    if handler is None:
        raise ToolDesconhecidaError(tool_name)
    return handler(args)
