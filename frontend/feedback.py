"""Tratamento padronizado de loading e erros (Stephanie #8, RNF-10).

Duas frentes:

1. `chamar_com_loading(funcao, mensagem)` envelopa qualquer chamada ao
   backend em `st.spinner`, garantindo feedback visual enquanto a API
   responde. Eh um helper fino — quem precisa de spinner mais elaborado
   pode usar `st.spinner` direto.

2. `mensagem_erro_para_bot(erro)` converte uma `APIError` em texto pt-br
   pronto para virar mensagem do bot no historico do chat (RNF-10:
   "renderizacao de erro da API como mensagem do bot"). Caller decide se
   acrescenta no historico ou exibe via `st.error` (ex.: tela de login).
"""
from typing import Any, Callable

import streamlit as st

from cliente import APIError


def chamar_com_loading(
    funcao: Callable[[], Any],
    mensagem: str = "Carregando...",
) -> Any:
    """Executa `funcao()` dentro de `st.spinner(mensagem)`.

    Repassa qualquer excecao para o caller — o spinner so cuida do
    feedback visual; o tratamento de APIError continua no caller.
    """
    with st.spinner(mensagem):
        return funcao()


def mensagem_erro_para_bot(erro: APIError) -> str:
    """Formata uma APIError como texto que o bot exibe no chat.

    Status 0 (servidor fora) recebe um prefixo claro; demais codigos
    apenas mostram o detail vindo do backend (C3). O texto e curto e em
    pt-br para caber bem em uma bolha de chat.
    """
    if erro.status == 0:
        return f"⚠️ {erro.detail}"
    return f"⚠️ Não consegui completar a ação: {erro.detail}"
