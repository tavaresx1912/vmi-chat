"""Fallback de ambiguidade (PRD §11.5).

Quando o Gemini nao emite uma function call (ou o intent ficou ambiguo),
o bot responde com uma mensagem listando as opcoes disponiveis para o
papel atual — sem "adivinhar". Este modulo encapsula essa mensagem.

A lista de tools visiveis ja vem do filtro por papel
(`nlu.filtro_tools.tools_para_papel`); aqui so traduzimos cada nome em
uma frase curta em pt-br entendivel para o usuario final.
"""
from typing import Any

from .filtro_tools import tools_para_papel


# Frase curta em 1a pessoa para cada tool. Cobre o catalogo completo
# dos tres papeis (PRD §11.3). Tools que aparecam aqui mas nao no mapa
# sao mostradas pelo nome cru — degradacao controlada.
_DESCRICOES: dict[str, str] = {
    # Admin
    "criar_usuario": "criar um novo usuário",
    "listar_usuarios": "listar usuários cadastrados",
    "desativar_usuario": "desativar um usuário",
    # Usuario
    "buscar_produtos": "buscar produtos no catálogo",
    "cadastrar_produto": "cadastrar um produto",
    "consultar_estoque": "consultar seu estoque",
    "configurar_pontos_reposicao": "configurar pontos de reposição",
    "criar_pedido_manual": "criar um pedido manual",
    "pedido_reposicao": "solicitar reposição automática",
    "listar_pedidos": "listar seus pedidos",
    # Fornecedor
    "atualizar_estoque": "atualizar o estoque de um cliente",
    "atualizar_status_pedido": "atualizar o status de um pedido",
}


def mensagem_fallback(role: str | None) -> str:
    """Devolve a mensagem de fallback para o papel informado.

    Sessao sem papel autenticado recebe orientacao generica — esse caso
    nao deveria chegar ate o NLU, mas tratar e barato.
    """
    if role is None:
        return (
            "Não entendi sua solicitação. Faça login para que eu possa "
            "listar as opções disponíveis."
        )

    tools = tools_para_papel(role)
    if not tools:
        return (
            "Não entendi sua solicitação e não encontrei opções "
            "disponíveis para o seu papel."
        )

    linhas = _formatar_opcoes(tools)
    return (
        "Não entendi exatamente o que você quer. Você pode pedir, por "
        "exemplo:\n" + linhas
    )


def _formatar_opcoes(tools: list[dict[str, Any]]) -> str:
    """Monta a lista bullet com a descricao pt-br de cada tool.

    Mantemos a ordem definida em tools_*.py (que ja segue o PRD §11.3) —
    sem reordenar (R-ALG-02 nao se aplica: nao ha criterio de ordenacao,
    so iteracao na ordem do catalogo).
    """
    partes: list[str] = []
    for decl in tools:
        nome = decl["name"]
        descricao = _DESCRICOES.get(nome, nome)
        partes.append(f"- {descricao}")
    return "\n".join(partes)
