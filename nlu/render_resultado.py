"""Renderizacao dos resultados das tools como texto pt-br para o chat.

O backend devolve JSON; o usuario quer ler uma frase. Para cada tool,
um handler converte a resposta em uma mensagem curta. Tools sem handler
cairao no formatador generico (`_fallback`) — JSON enxuto, melhor que
nada mas nao recomendado.
"""
from typing import Any, Callable


def _fmt_user(u: dict[str, Any]) -> str:
    ativo = "ativo" if u.get("ativo", True) else "inativo"
    return f"#{u['id']} {u['nome']} <{u['email']}> [{u['role']}, {ativo}]"


def _fmt_produto(p: dict[str, Any]) -> str:
    return f"#{p['id']} {p['nome']} ({p['categoria']})"


def _fmt_estoque_item(e: dict[str, Any]) -> str:
    return (
        f"#{e['produto_id']}: {e['quantidade']} un. — {e['status']}"
    )


def _fmt_pedido(p: dict[str, Any]) -> str:
    return (
        f"#{p['id']} [{p['status']}] origem={p['origem']} "
        f"em {p.get('criado_em', '?')}"
    )


def _r_listar_usuarios(r: list[dict[str, Any]]) -> str:
    if not r:
        return "Nenhum usuário encontrado."
    linhas = [f"- {_fmt_user(u)}" for u in r]
    return f"{len(r)} usuário(s):\n" + "\n".join(linhas)


def _r_criar_usuario(r: dict[str, Any]) -> str:
    return f"Usuário criado: {_fmt_user(r)}"


def _r_desativar_usuario(r: dict[str, Any]) -> str:
    return f"Usuário desativado: {_fmt_user(r)}"


def _r_buscar_produtos(r: list[dict[str, Any]]) -> str:
    if not r:
        return "Nenhum produto encontrado."
    linhas = [f"- {_fmt_produto(p)}" for p in r]
    return f"{len(r)} produto(s):\n" + "\n".join(linhas)


def _r_cadastrar_produto(r: dict[str, Any]) -> str:
    return (
        f"Produto cadastrado e vinculado: contrato #{r['id']}, "
        f"produto #{r['produto_id']}, fornecedor #{r['fornecedor_id']}."
    )


def _r_consultar_estoque(r: list[dict[str, Any]]) -> str:
    if not r:
        return "Estoque vazio."
    linhas = [f"- {_fmt_estoque_item(e)}" for e in r]
    return f"Estoque ({len(r)} itens):\n" + "\n".join(linhas)


def _r_configurar_pontos(r: dict[str, Any]) -> str:
    return (
        f"Pontos configurados para produto #{r['produto_id']}: "
        f"vermelho<={r['ponto_reposicao']}, "
        f"amarelo<={r['ponto_amarelo']}."
    )


def _r_pedido_criado(r: dict[str, Any]) -> str:
    itens = r.get("itens", [])
    return (
        f"Pedido #{r['id']} criado com {len(itens)} item(ns), "
        f"status {r['status']}."
    )


def _r_listar_pedidos(r: list[dict[str, Any]]) -> str:
    if not r:
        return "Nenhum pedido encontrado."
    linhas = [f"- {_fmt_pedido(p)}" for p in r]
    return f"{len(r)} pedido(s):\n" + "\n".join(linhas)


def _r_atualizar_estoque(r: dict[str, Any]) -> str:
    return (
        f"Estoque atualizado: produto #{r['produto_id']} "
        f"agora com {r['quantidade']} un. ({r['status']})."
    )


def _r_atualizar_status_pedido(r: dict[str, Any]) -> str:
    return f"Pedido #{r['id']} agora está {r['status']}."


_HANDLERS: dict[str, Callable[[Any], str]] = {
    "criar_usuario": _r_criar_usuario,
    "listar_usuarios": _r_listar_usuarios,
    "desativar_usuario": _r_desativar_usuario,
    "buscar_produtos": _r_buscar_produtos,
    "cadastrar_produto": _r_cadastrar_produto,
    "consultar_estoque": _r_consultar_estoque,
    "configurar_pontos_reposicao": _r_configurar_pontos,
    "criar_pedido_manual": _r_pedido_criado,
    "pedido_reposicao": _r_pedido_criado,
    "listar_pedidos": _r_listar_pedidos,
    "atualizar_estoque": _r_atualizar_estoque,
    "atualizar_status_pedido": _r_atualizar_status_pedido,
}


def _fallback(resposta: Any) -> str:
    """Render generico quando nao ha handler — evita JSON cru gigante."""
    if resposta is None:
        return "Ação concluída."
    return f"Resultado: {resposta}"


def formatar_resultado(tool: str, resposta: Any) -> str:
    """Devolve texto pt-br para a resposta da API de uma tool.

    Erros de schema na resposta (ex.: chave ausente) caem para o
    fallback generico — o usuario nao deve ver KeyError, ainda que o
    texto fique mais cru. O caller (orquestrador) tambem ja capturou
    APIError antes; aqui so chega resposta de 2xx.
    """
    handler = _HANDLERS.get(tool)
    if handler is None:
        return _fallback(resposta)
    try:
        return handler(resposta)
    except (KeyError, TypeError, IndexError):
        return _fallback(resposta)
