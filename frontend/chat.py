"""Renderizacao do historico de chat (Stephanie #6, RNF-16).

A lista `historico` do C7 guarda as mensagens trocadas na sessao atual,
sem persistencia entre sessoes. Cada mensagem segue o formato minimo:

    {"autor": "usuario" | "bot", "texto": str}

Branches futuras (cartao de confirmacao, fallback) podem estender o dict
com chaves opcionais — autor/texto ficam como contrato basico que o
renderer entende.
"""
from typing import Any

import streamlit as st


# Mapa autor -> rotulo aceito por st.chat_message. Streamlit aceita
# strings arbitrarias, mas "user" e "assistant" tem avatares padrao,
# entao traduzimos as chaves do C7 para esses rotulos.
_ROTULO_CHAT_MESSAGE: dict[str, str] = {
    "usuario": "user",
    "bot": "assistant",
}


def renderizar_historico(historico: list[dict[str, Any]]) -> None:
    """Renderiza cada mensagem do historico como bolha de chat.

    Mensagens com autor desconhecido sao ignoradas silenciosamente — e
    melhor nao quebrar a UI por causa de um item malformado.
    """
    for mensagem in historico:
        autor = mensagem.get("autor")
        texto = mensagem.get("texto", "")
        rotulo = _ROTULO_CHAT_MESSAGE.get(autor or "")
        if rotulo is None:
            continue
        with st.chat_message(rotulo):
            st.markdown(texto)


def acrescentar_mensagem(
    historico: list[dict[str, Any]],
    autor: str,
    texto: str,
) -> None:
    """Adiciona uma mensagem ao final do historico (mutacao in-place).

    Wrapper fino para manter o formato {"autor", "texto"} em um unico
    lugar — outras camadas (futuro wiring com Gemini) chamam essa funcao
    em vez de acessar o dict diretamente.
    """
    historico.append({"autor": autor, "texto": texto})
