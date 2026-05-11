"""Entry point da aplicacao Streamlit do VMI Chat.

Inicializa a sessao (C7) e roteia entre tela de login e area autenticada
com base na presenca de JWT no session_state.
"""
import streamlit as st

from login import mostrar_tela_login
from sessao import inicializar_sessao

st.set_page_config(page_title="VMI Chat")

inicializar_sessao(st.session_state)

if st.session_state["jwt"] is None:
    mostrar_tela_login()
else:
    st.title("VMI Chat")
    st.write(
        f"Autenticado como **{st.session_state['role']}** "
        f"(user_id={st.session_state['user_id']})."
    )
    st.caption("Layout pós-login chega nas próximas branches.")
