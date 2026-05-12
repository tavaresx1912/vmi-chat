"""Cartao de confirmacao para acoes de escrita (Stephanie #7, RNF-13).

Fluxo (PRD §11.4):
    1. Gemini devolve function call -> Stephanie chama
       `solicitar_confirmacao(tool, args)`.
    2. Proximo render de `_renderizar_chat` exibe o cartao com o
       texto-resumo (C5, `nlu.resumos.gerar_resumo_acao`) e dois botoes:
       "Confirmar" e "Cancelar".
    3. Em "Confirmar", o callback recebido executa a chamada HTTP real;
       em "Cancelar", a acao e descartada com mensagem do bot.

Estado pendente vive em `st.session_state["pendente_confirmacao"]`
(extensao do C7, dono: Stephanie). Sempre que houver pendente, o input
do chat fica bloqueado — uma acao por vez.

Tools de leitura nao passam por aqui (ToolSomenteLeituraError do C5);
o caller deve filtrar e despachar direto.
"""
from typing import Any, Callable

import streamlit as st

from chat import acrescentar_mensagem
from nlu.resumos import (
    ToolDesconhecidaError,
    ToolSomenteLeituraError,
    gerar_resumo_acao,
)


# Chave fixa em session_state para a acao aguardando confirmacao.
# Valor: dict {"tool": str, "args": dict, "resumo": str} ou None.
_CHAVE_PENDENTE = "pendente_confirmacao"


def ha_pendente() -> bool:
    """True se existe acao aguardando confirmacao na sessao."""
    return st.session_state.get(_CHAVE_PENDENTE) is not None


def solicitar_confirmacao(tool: str, args: dict[str, Any]) -> None:
    """Registra uma acao de escrita pendente, gerando o texto-resumo via C5.

    Levanta ToolSomenteLeituraError/ToolDesconhecidaError vindas de C5 —
    o caller decide o que mostrar (em geral, uma mensagem do bot).
    """
    resumo = gerar_resumo_acao(tool, args)  # pode levantar; deixa subir
    st.session_state[_CHAVE_PENDENTE] = {
        "tool": tool,
        "args": args,
        "resumo": resumo,
    }


def _limpar_pendente() -> None:
    st.session_state[_CHAVE_PENDENTE] = None


def renderizar_cartao(
    on_confirmar: Callable[[str, dict[str, Any]], str],
) -> None:
    """Renderiza o cartao se houver pendente; no-op caso contrario.

    `on_confirmar(tool, args)` e chamado quando o usuario clica
    "Confirmar"; deve devolver o texto curto a acrescentar no historico
    como mensagem do bot (ex.: "Pedido criado com sucesso."). Excecoes
    do callback NAO sao tratadas aqui — quem chama o backend usa o
    helper de feedback (Stephanie #8) para mapear erros.
    """
    pendente = st.session_state.get(_CHAVE_PENDENTE)
    if pendente is None:
        return

    with st.chat_message("assistant"):
        st.markdown(pendente["resumo"])
        col_ok, col_cancel = st.columns(2)
        confirmar = col_ok.button("Confirmar", key="btn_confirmar_acao")
        cancelar = col_cancel.button("Cancelar", key="btn_cancelar_acao")

    if confirmar:
        tool = pendente["tool"]
        args = pendente["args"]
        _limpar_pendente()
        resposta = on_confirmar(tool, args)
        acrescentar_mensagem(
            st.session_state["historico"], "bot", resposta
        )
        st.rerun()
    elif cancelar:
        _limpar_pendente()
        acrescentar_mensagem(
            st.session_state["historico"], "bot", "Ação cancelada."
        )
        st.rerun()


# Re-export para callers conseguirem capturar os erros sem importar de nlu.
__all__ = [
    "ha_pendente",
    "solicitar_confirmacao",
    "renderizar_cartao",
    "ToolDesconhecidaError",
    "ToolSomenteLeituraError",
]
