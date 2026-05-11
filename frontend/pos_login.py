"""Layout pos-login (Stephanie #4) + botao de logout (#9).

Renderiza o shell autenticado: header com info do usuario + duas colunas
(chat a esquerda, painel a direita). Inclui botao de logout no header.
"""
import streamlit as st

from sessao import fazer_logout


def mostrar_pos_login() -> None:
    """Renderiza o shell autenticado com chat + painel lateral."""
    role = st.session_state.get("role") or "?"
    _renderizar_header(role)

    coluna_chat, coluna_painel = st.columns([3, 1])

    with coluna_chat:
        _renderizar_chat()

    with coluna_painel:
        _renderizar_painel()


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
    """Coluna esquerda: placeholder de mensagens + input no rodape."""
    st.subheader("Chat")
    st.caption("Histórico de mensagens aparece aqui (próximas branches).")
    # Renderiza o input sem capturar o valor — wiring com NLU vem em
    # branch futura, fora do escopo deste layout.
    st.chat_input("Digite sua mensagem...")


def _renderizar_painel() -> None:
    """Coluna direita: placeholder do semaforo Kanban (RN-06)."""
    st.subheader("Estoque")
    st.caption("Semáforo Kanban aparece aqui (branch `painel-semaforo`).")
