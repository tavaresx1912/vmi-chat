"""Orquestrador da conversa (PRD §11.4) — wiring Streamlit <-> Gemini <-> backend.

Fluxo executado a cada mensagem do usuario:

    sanitiza -> monta prompt -> filtra tools por papel -> Gemini ->
      (sem function call) bot escreve mensagem_fallback
      (tool de leitura) executa + render_resultado
      (tool de escrita) abre cartao de confirmacao; on_confirmar executa

Erros HTTP viram mensagem do bot via `mensagem_erro_para_bot` (RNF-10).
Falha de API key do Gemini idem — o app nao crasha.

Conversao dos args da function call do SDK do google-generativeai:
o objeto retornado e um `proto.marshal.collections.maps.MapComposite`,
convertivel via `dict()` recursivamente. `_args_to_dict` cuida disso.
"""
from typing import Any

import streamlit as st

from chat import acrescentar_mensagem
from cliente import APIError, request as http_request
from feedback import chamar_com_loading, mensagem_erro_para_bot

from nlu.client import get_client
from nlu.dispatch import (
    ArgsInvalidosError,
    ToolForaDoEscopoError,
    executar_tool,
)
from nlu.fallback import mensagem_fallback
from nlu.filtro_tools import tools_para_papel
from nlu.prompts import build_prompt
from nlu.render_resultado import formatar_resultado
from nlu.resumos import ToolSomenteLeituraError, gerar_resumo_acao
from nlu.sanitizacao import sanitizar_entrada_usuario

from cartao_confirmacao import solicitar_confirmacao


# Tools de leitura: nao passam por cartao de confirmacao (RNF-13). Lista
# espelhada do _LEITURAS de nlu/resumos.py — em vez de importar privado,
# repetimos aqui porque a politica "leitura nao confirma" e do
# orquestrador, nao do resumo.
_LEITURAS: frozenset[str] = frozenset(
    {
        "listar_usuarios",
        "buscar_produtos",
        "consultar_estoque",
        "listar_pedidos",
    }
)


def _args_to_dict(valor: Any) -> Any:
    """Converte MapComposite/RepeatedComposite do proto-plus em dict/list nativos."""
    # MapComposite expoe .items(); RepeatedComposite e iteravel sem .items().
    if hasattr(valor, "items"):
        return {k: _args_to_dict(v) for k, v in valor.items()}
    if isinstance(valor, str) or not hasattr(valor, "__iter__"):
        return valor
    return [_args_to_dict(v) for v in valor]


def _http_call(metodo: str, path: str, body: Any, params: dict | None) -> Any:
    """Adaptador entre `nlu.dispatch.executar_tool` e o cliente do frontend."""
    return http_request(metodo, path, json=body, params=params)


def processar_mensagem(texto_usuario: str) -> None:
    """Trata a entrada do usuario rodando o fluxo §11.4 completo.

    Acrescenta a mensagem do usuario ao historico e, dependendo da
    resposta do Gemini, abre cartao de confirmacao ou ja escreve a
    resposta do bot.
    """
    historico = st.session_state["historico"]
    role = st.session_state.get("role")

    # 1. Sanitizacao (RNF-15). Erro vira mensagem do bot.
    try:
        texto_limpo = sanitizar_entrada_usuario(texto_usuario)
    except ValueError as e:
        acrescentar_mensagem(historico, "usuario", texto_usuario)
        acrescentar_mensagem(historico, "bot", f"⚠️ {e}")
        return

    acrescentar_mensagem(historico, "usuario", texto_limpo)

    # 2. Monta prompt com filtro de tools por papel.
    tools = tools_para_papel(role)
    prompt = build_prompt(
        papel=role or "desconhecido",
        nome=str(st.session_state.get("user_id") or "?"),
        entrada_usuario=texto_limpo,
    )

    # 3. Chama Gemini.
    try:
        client = get_client()
        resposta = chamar_com_loading(
            lambda: client.generate_content(
                prompt, tools=[{"function_declarations": tools}] if tools else None
            ),
            "Pensando...",
        )
    except RuntimeError as e:  # GEMINI_API_KEY ausente
        acrescentar_mensagem(historico, "bot", f"⚠️ {e}")
        return
    except Exception as e:  # falha de rede/SDK; nao crasha o app
        acrescentar_mensagem(
            historico, "bot", f"⚠️ Erro ao consultar o assistente: {e}"
        )
        return

    # 4. Extrai function call, se houver.
    function_call = _extrair_function_call(resposta)
    if function_call is None:
        acrescentar_mensagem(historico, "bot", mensagem_fallback(role))
        return

    tool_name = function_call.name
    args = _args_to_dict(function_call.args)

    # 5. Leitura: executa direto. Escrita: cartao de confirmacao.
    if tool_name in _LEITURAS:
        _executar_e_renderizar(tool_name, args, role, historico)
    else:
        try:
            # gerar_resumo_acao valida que e tool de escrita conhecida.
            gerar_resumo_acao(tool_name, args)
        except ToolSomenteLeituraError:
            # Tool nao listada em _LEITURAS mas marcada como leitura no resumo
            # — defensivo, nao deveria ocorrer.
            _executar_e_renderizar(tool_name, args, role, historico)
            return
        except Exception as e:
            acrescentar_mensagem(
                historico, "bot", f"⚠️ Não consegui interpretar a ação: {e}"
            )
            return
        solicitar_confirmacao(tool_name, args)


def _extrair_function_call(resposta: Any) -> Any:
    """Devolve o primeiro FunctionCall encontrado nas partes da resposta, ou None."""
    try:
        candidates = resposta.candidates
        if not candidates:
            return None
        partes = candidates[0].content.parts
    except (AttributeError, IndexError):
        return None
    for parte in partes:
        fc = getattr(parte, "function_call", None)
        if fc is not None and getattr(fc, "name", ""):
            return fc
    return None


def _executar_e_renderizar(
    tool: str, args: dict, role: str | None, historico: list
) -> None:
    """Executa a tool via dispatch + traduz resultado/erro em mensagem do bot."""
    if role is None:
        acrescentar_mensagem(historico, "bot", "⚠️ Sessão sem papel.")
        return
    try:
        resultado = chamar_com_loading(
            lambda: executar_tool(
                tool=tool,
                args=args,
                role=role,
                http_call=_http_call,
            ),
            "Executando...",
        )
    except (ToolForaDoEscopoError, ArgsInvalidosError) as e:
        acrescentar_mensagem(historico, "bot", f"⚠️ {e}")
        return
    except APIError as e:
        acrescentar_mensagem(historico, "bot", mensagem_erro_para_bot(e))
        return
    acrescentar_mensagem(historico, "bot", formatar_resultado(tool, resultado))


def executar_acao_confirmada(tool: str, args: dict) -> str:
    """Callback do cartao de confirmacao para tools de escrita.

    Devolve o texto que o cartao acrescenta como mensagem do bot. Erros
    de API/dispatch viram texto formatado — o cartao nao precisa saber
    da existencia de APIError.
    """
    role = st.session_state.get("role")
    if role is None:
        return "⚠️ Sessão sem papel."
    try:
        resultado = chamar_com_loading(
            lambda: executar_tool(
                tool=tool,
                args=args,
                role=role,
                http_call=_http_call,
            ),
            "Executando...",
        )
    except (ToolForaDoEscopoError, ArgsInvalidosError) as e:
        return f"⚠️ {e}"
    except APIError as e:
        return mensagem_erro_para_bot(e)
    return formatar_resultado(tool, resultado)
