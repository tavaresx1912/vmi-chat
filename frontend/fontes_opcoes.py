"""Fontes de opcoes para os dropdowns dos formularios em chat.

Cada `fonte_dropdown` declarado em `nlu.formularios.CAMPOS_POR_TOOL`
mapeia para uma funcao aqui que chama o endpoint correspondente e
devolve lista de `(valor, label)`. Resultados sao cacheados em
`st.session_state["opcoes_cache"]` para evitar refetch a cada rerun do
Streamlit; `invalidar(fonte)` ou `limpar_cache()` forcam refresh apos
uma escrita que altera a fonte.

APIError nao e engolido — o caller (cartao_confirmacao) decide o que
mostrar quando uma fonte falha (ex.: substituir dropdown por aviso).
"""
from typing import Any, Callable

import streamlit as st

from cliente import get as http_get


OpcaoTupla = tuple[Any, str]
_CHAVE_CACHE = "opcoes_cache"


def opcoes_para(fonte: str) -> list[OpcaoTupla]:
    """Devolve as opcoes da `fonte` declarada na spec.

    KeyError se a fonte for desconhecida — indica bug de spec (Campo com
    fonte_dropdown que ninguem implementou aqui).
    """
    fetcher = _FONTES.get(fonte)
    if fetcher is None:
        raise KeyError(f"Fonte de opcoes desconhecida: {fonte}")
    return _cache_ou_fetch(fonte, fetcher)


def invalidar(fonte: str) -> None:
    """Remove a entrada da fonte; proximo opcoes_para refaz o GET."""
    cache = st.session_state.get(_CHAVE_CACHE) or {}
    cache.pop(fonte, None)
    st.session_state[_CHAVE_CACHE] = cache


def limpar_cache() -> None:
    """Esvazia o cache (uso: logout, troca de papel)."""
    st.session_state[_CHAVE_CACHE] = {}


def _cache_ou_fetch(
    fonte: str, fetcher: Callable[[], list[OpcaoTupla]]
) -> list[OpcaoTupla]:
    cache = st.session_state.get(_CHAVE_CACHE) or {}
    if fonte in cache:
        return cache[fonte]
    valor = fetcher()
    cache[fonte] = valor
    st.session_state[_CHAVE_CACHE] = cache
    return valor


# --- fetchers por endpoint ---


def _fetch_usuarios() -> list[OpcaoTupla]:
    """/admin/usuarios -> [(id, "Nome <email>")]; filtra inativos.

    desativar_usuario sobre alguem ja inativo seria no-op no backend
    (idempotente) mas confunde a UX, entao filtramos aqui.
    """
    data = http_get("/admin/usuarios") or []
    saida: list[OpcaoTupla] = []
    for u in data:
        if u.get("ativo") is False:
            continue
        nome = u.get("nome", "?")
        email = u.get("email", "?")
        saida.append((u["id"], f"{nome} <{email}>"))
    return saida


def _fetch_fornecedores() -> list[OpcaoTupla]:
    """/usuario/fornecedores -> [(id, "Nome (CNPJ XX)")]."""
    data = http_get("/usuario/fornecedores") or []
    saida: list[OpcaoTupla] = []
    for f in data:
        saida.append(
            (
                f["id"],
                f"{f.get('nome', '?')} (CNPJ {f.get('cnpj', '?')})",
            )
        )
    return saida


def _fetch_produtos_catalogo() -> list[OpcaoTupla]:
    """/usuario/produtos -> [(id, "Nome - Categoria")] do catalogo completo."""
    data = http_get("/usuario/produtos") or []
    saida: list[OpcaoTupla] = []
    for p in data:
        nome = p.get("nome", "?")
        categoria = p.get("categoria", "")
        label = f"{nome}" + (f" — {categoria}" if categoria else "")
        saida.append((p["id"], label))
    return saida


def _fetch_produtos_estoque() -> list[OpcaoTupla]:
    """/usuario/estoque + /usuario/produtos -> [(produto_id, "Nome - status")].

    Faz join client-side porque EstoqueComStatusRead nao inclui produto_nome.
    Para um catalogo de dezenas de produtos por usuario o custo e
    desprezivel; se crescer, vale enriquecer o response no backend.
    """
    estoque = http_get("/usuario/estoque") or []
    if not estoque:
        return []
    produtos = http_get("/usuario/produtos") or []
    nomes: dict[int, str] = {p["id"]: p.get("nome", "?") for p in produtos}
    saida: list[OpcaoTupla] = []
    for item in estoque:
        produto_id = item.get("produto_id")
        if produto_id is None:
            continue
        nome = nomes.get(produto_id, "?")
        status = item.get("status", "")
        label = f"{nome}" + (f" — {status}" if status else "")
        saida.append((produto_id, label))
    return saida


def _fetch_produtos_fornecedores() -> list[OpcaoTupla]:
    """/usuario/produtos-fornecedores -> [(pf_id, "Produto (Fornecedor) — R$ X, min N")]."""
    data = http_get("/usuario/produtos-fornecedores") or []
    saida: list[OpcaoTupla] = []
    for pf in data:
        label = (
            f"{pf.get('produto_nome', '?')} "
            f"({pf.get('fornecedor_nome', '?')}) "
            f"— R$ {pf.get('preco_contratado', '?')}, "
            f"min {pf.get('qtd_minima_pedido', '?')}"
        )
        saida.append((pf["id"], label))
    return saida


_FONTES: dict[str, Callable[[], list[OpcaoTupla]]] = {
    "usuarios": _fetch_usuarios,
    "fornecedores": _fetch_fornecedores,
    "produtos_catalogo": _fetch_produtos_catalogo,
    "produtos_estoque": _fetch_produtos_estoque,
    "produtos_fornecedores": _fetch_produtos_fornecedores,
}
