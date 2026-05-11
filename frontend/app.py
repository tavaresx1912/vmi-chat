"""Entry point da aplicacao Streamlit do VMI Chat.

Inicializa a sessao (contrato C7) e mostra a tela inicial. Tela de login
e fluxo pos-autenticacao chegam nas proximas branches da Stephanie.
"""
import streamlit as st

from sessao import inicializar_sessao

st.set_page_config(page_title="VMI Chat")

inicializar_sessao(st.session_state)

st.title("VMI Chat")
st.write("Faça login para continuar.")
