"""Layout pos-login (Stephanie #4) + logout (#9) + painel semaforo (#5).

Renderiza o shell autenticado: header com info do usuario + duas colunas
(chat a esquerda, painel a direita). O conteudo do painel direito
despacha por papel — apenas Usuario ve o semaforo de estoque (RN-06).
"""

import streamlit as st

from cartao_confirmacao import ha_pendente, renderizar_cartao
from chat import renderizar_historico
from orquestrador import executar_acao_confirmada, processar_mensagem
from painel_semaforo import mostrar_painel_semaforo
from sessao import fazer_logout


def mostrar_pos_login() -> None:
    """Renderiza o shell autenticado com chat + painel lateral."""
    role = st.session_state.get("role") or "?"
    _renderizar_header(role)

    coluna_chat, coluna_painel = st.columns([3, 1])

    with coluna_chat:
        _renderizar_chat()

    with coluna_painel:
        _renderizar_painel(role)


def _renderizar_header(role: str) -> None:
    """Header com titulo + badge do papel + botao de logout."""
    esquerda, direita = st.columns([3, 1])
    with esquerda:
        st.title("VMI Chat")
    with direita:
        st.markdown(f"Logado como **{role}**")
        if st.button("Sair", key="btn_logout"):
            fazer_logout(st.session_state)
            st.rerun()


def _renderizar_chat() -> None:
    """Coluna esquerda: historico de mensagens + input no rodape.

    Cada entrada do usuario passa pelo orquestrador, que conversa com o
    Gemini e despacha tools para o backend (PRD §11.4).
    """
    st.subheader("Chat")
    historico = st.session_state["historico"]
    renderizar_historico(historico)

    # Cartao de confirmacao (RNF-13): aparece quando ha acao pendente.
    renderizar_cartao(on_confirmar=executar_acao_confirmada)

    # Bloqueia a entrada enquanto ha acao pendente — uma acao por vez.
    if ha_pendente():
        st.chat_input(
            "Confirme ou cancele a ação acima para continuar...",
            disabled=True,
        )
        return

    entrada = st.chat_input("Digite sua mensagem...")
    if entrada:
        processar_mensagem(entrada)
        st.rerun()


def _renderizar_painel(role: str) -> None:
    """Coluna direita: semaforo Kanban se Usuario; placeholder caso contrario."""
    st.subheader("Estoque")
    if role == "usuario":
        mostrar_painel_semaforo()
    else:
        st.caption("Painel de estoque exclusivo para o papel Usuário.")
