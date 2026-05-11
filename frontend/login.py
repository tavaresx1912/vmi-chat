"""Tela de login (Stephanie #2).

Renderiza o formulario e chama POST /auth/login no backend. Em sucesso,
popula st.session_state com os campos do C7 (`jwt`, `user_id`, `role`).
A chamada httpx aqui e direta — o wrapper generico chega em `cliente-http`.
"""
import os

import httpx
import streamlit as st


# Default local-dev. Em deploy real, definir BACKEND_URL no ambiente.
_BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


def _autenticar(email: str, senha: str) -> tuple[bool, str]:
    """Chama POST /auth/login e popula session_state em sucesso.

    Retorna (sucesso, mensagem_pt_br). Mensagens sao prontas para exibir;
    nao expoem o `detail` cru do backend em 401 (UX), mas repassam o
    detail em outros codigos de erro inesperados.
    """
    try:
        resp = httpx.post(
            f"{_BACKEND_URL}/auth/login",
            json={"email": email, "senha": senha},
            timeout=10.0,
        )
    except httpx.RequestError:
        return False, "Servidor indisponível. Tente novamente em alguns instantes."

    if resp.status_code == 200:
        data = resp.json()
        st.session_state["jwt"] = data["access_token"]
        st.session_state["user_id"] = data["user_id"]
        st.session_state["role"] = data["role"]
        return True, ""

    if resp.status_code == 401:
        return False, "E-mail ou senha inválidos."

    # Outros erros: extrai `detail` no formato C3, com fallback defensivo.
    try:
        detail = resp.json().get("detail", "Erro desconhecido")
    except ValueError:
        detail = "Erro desconhecido"
    return False, f"Erro no login: {detail}"


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
