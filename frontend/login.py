"""Tela de login (Stephanie #2 + cliente-http refactor).

Renderiza o formulario e chama POST /auth/login pelo wrapper httpx
(`cliente.post`). Em sucesso, popula st.session_state com os campos do
C7 (`jwt`, `user_id`, `role`).
"""
import streamlit as st

from cliente import APIError, post
from feedback import chamar_com_loading


def _autenticar(email: str, senha: str) -> tuple[bool, str]:
    """Chama POST /auth/login e popula session_state em sucesso.

    Retorna (sucesso, mensagem_pt_br). Mensagens sao prontas para exibir;
    nao expoem o `detail` cru do backend em 401 (UX).
    """
    try:
        data = chamar_com_loading(
            lambda: post(
                "/auth/login",
                json={"email": email, "senha": senha},
                auth=False,
            ),
            "Autenticando...",
        )
    except APIError as e:
        if e.status == 0:
            return False, e.detail
        if e.status == 401:
            return False, "E-mail ou senha inválidos."
        return False, f"Erro no login: {e.detail}"

    st.session_state["jwt"] = data["access_token"]
    st.session_state["user_id"] = data["user_id"]
    st.session_state["role"] = data["role"]
    return True, ""


def mostrar_tela_login() -> None:
    """Renderiza a tela de login e processa o submit do formulario."""
    st.title("VMI Chat")
    st.subheader("Login")

    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

    if not submit:
        return

    if not email or not senha:
        st.error("Preencha e-mail e senha.")
        return

    sucesso, mensagem = _autenticar(email, senha)
    if sucesso:
        st.rerun()
    else:
        st.error(mensagem)
