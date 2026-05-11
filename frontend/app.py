"""Entry point da aplicacao Streamlit do VMI Chat.

Inicializa a sessao (C7) e roteia entre tela de login e shell pos-login
com base na presenca de JWT no session_state.
"""
import streamlit as st

from login import mostrar_tela_login
from pos_login import mostrar_pos_login
from sessao import inicializar_sessao

# layout='wide' libera a largura do browser para acomodar bem o
# layout de duas colunas (chat 3 : painel 1) do pos-login.
st.set_page_config(page_title="VMI Chat", layout="wide")

inicializar_sessao(st.session_state)

if st.session_state["jwt"] is None:
    mostrar_tela_login()
else:
    mostrar_pos_login()
