"""Painel lateral com semaforo Kanban (RN-06).

Consome dois endpoints:
- GET /usuario/estoque  -> linhas com `status` (verde/amarelo/vermelho)
- GET /usuario/produtos -> catalogo (para resolver produto_id -> nome)

Render compacto, pensado para a coluna estreita do layout pos-login:
cabecalho colorido por grupo + contagem + lista enxuta de items.
"""
import streamlit as st

from cliente import APIError, get


# Ordem fixa do painel (Verde -> Amarelo -> Vermelho), do menos para o
# mais critico. Cabe a colunal estreita do layout sem precisar de scroll
# em estoques pequenos.
_GRUPOS = ("verde", "amarelo", "vermelho")
_HEADERS = {
    "verde": ":green[**Verde**]",
    "amarelo": ":orange[**Amarelo**]",
    "vermelho": ":red[**Vermelho**]",
}


def mostrar_painel_semaforo() -> None:
    """Renderiza o painel completo. Caller garante role == 'usuario'."""
    try:
        estoque = get("/usuario/estoque")
        produtos = get("/usuario/produtos")
    except APIError as e:
        if e.status == 0:
            st.warning("Servidor indisponível.")
        else:
            st.warning(f"Erro ao carregar estoque: {e.detail}")
        return

    if not estoque:
        st.info("Nenhum item no estoque ainda.")
        return

    # Mapa id -> nome para mostrar o produto em vez de produto_id cru.
    nome_por_id: dict[int, str] = {p["id"]: p["nome"] for p in produtos}

    # Agrupa por status mantendo a ordem original (insertion order do dict).
    por_status: dict[str, list[dict]] = {g: [] for g in _GRUPOS}
    for item in estoque:
        por_status[item["status"]].append(item)

    for grupo in _GRUPOS:
        items = por_status[grupo]
        st.markdown(f"{_HEADERS[grupo]} ({len(items)})")
        for it in items:
            nome = nome_por_id.get(it["produto_id"], f"#{it['produto_id']}")
            st.markdown(f"- {nome}: {it['quantidade']}")
