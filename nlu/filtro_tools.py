"""Filtragem do catalogo de tools pelo papel autenticado (C7 -> Ingrid).

PRD §11.3 define que cada papel so enxerga as tools do seu perfil. Antes
de montar o request para o Gemini, Stephanie chama
`tools_para_papel(role)` passando o valor de `st.session_state["role"]`
(contrato C7). Quem nao esta autenticado nao deve sequer chegar ate aqui;
ainda assim tratamos o caso como "nenhuma tool" para evitar vazamento.

Tambem expomos `schemas_args_para_papel` para que, quando o Gemini
devolver uma function call, os argumentos sejam validados com a classe
Pydantic correta — mesma logica do filtro, so trocando o mapa.
"""
from typing import Any

from pydantic import BaseModel

from .tools_admin import SCHEMAS_ARGS_ADMIN, TOOLS_ADMIN
from .tools_fornecedor import SCHEMAS_ARGS_FORNECEDOR, TOOLS_FORNECEDOR
from .tools_usuario import SCHEMAS_ARGS_USUARIO, TOOLS_USUARIO


# Mapas fechados papel -> catalogo. Sao tres papeis fixos do PRD §3, entao
# um dict simples e suficiente — nao ha busca em lista, nao se aplica
# R-ALG-01 aqui (acesso direto por chave, O(1) didatico).
_TOOLS_POR_PAPEL: dict[str, list[dict[str, Any]]] = {
    "admin": TOOLS_ADMIN,
    "usuario": TOOLS_USUARIO,
    "fornecedor": TOOLS_FORNECEDOR,
}

_SCHEMAS_POR_PAPEL: dict[str, dict[str, type[BaseModel]]] = {
    "admin": SCHEMAS_ARGS_ADMIN,
    "usuario": SCHEMAS_ARGS_USUARIO,
    "fornecedor": SCHEMAS_ARGS_FORNECEDOR,
}


def tools_para_papel(role: str | None) -> list[dict[str, Any]]:
    """Devolve as function declarations visiveis ao papel informado.

    Se `role` for None ou desconhecido, retorna lista vazia. Isso encerra
    qualquer tentativa de function call no Gemini para sessoes nao
    autenticadas, em vez de propagar uma excecao para a UI.
    """
    if role is None:
        return []
    return _TOOLS_POR_PAPEL.get(role, [])


def schemas_args_para_papel(
    role: str | None,
) -> dict[str, type[BaseModel]]:
    """Devolve o mapa nome_tool -> classe Pydantic visivel ao papel.

    Mesma politica de tools_para_papel: papel desconhecido retorna mapa
    vazio, o que faz a validacao de argumentos falhar de forma controlada
    (KeyError no chamador) caso o Gemini invente uma tool fora do escopo.
    """
    if role is None:
        return {}
    return _SCHEMAS_POR_PAPEL.get(role, {})
