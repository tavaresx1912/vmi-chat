"""Cartao de acao para tools de escrita (PRD §11.4 + UX).

Em vez de mostrar resumo textual + [Confirmar]/[Cancelar], renderiza um
formulario com os campos da tool (spec em `nlu.formularios`). Argumentos
extraidos pelo Gemini pre-preenchem os campos; o usuario completa,
edita e confirma. A validacao final acontece via classes Pydantic
*Args (executadas pelo dispatch no submit), entao erros de schema
viram mensagem do bot — o form nao tenta replicar a regra de negocio.

Estado pendente: `st.session_state["pendente_confirmacao"]` (extensao
do C7, dono: Stephanie). Sempre que houver pendente, o input do chat
fica bloqueado em pos_login (`ha_pendente()`).

Tools de leitura nao passam por aqui; o caller filtra e despacha
direto via `_executar_e_renderizar` do orquestrador.
"""
from typing import Any, Callable

import streamlit as st

from chat import acrescentar_mensagem
from fontes_opcoes import opcoes_para
from nlu.formularios import Campo, campos_de


# Chave fixa em session_state para a acao pendente.
# Valor: {"tool": str, "args": dict} ou None.
_CHAVE_PENDENTE = "pendente_confirmacao"


def ha_pendente() -> bool:
    """True se existe acao aguardando o usuario completar/confirmar."""
    return st.session_state.get(_CHAVE_PENDENTE) is not None


def solicitar_acao(tool: str, args: dict[str, Any]) -> None:
    """Registra uma acao pendente; o proximo render mostra o formulario."""
    st.session_state[_CHAVE_PENDENTE] = {"tool": tool, "args": args}


# Alias para manter retrocompatibilidade com callers que ainda usam o nome antigo.
solicitar_confirmacao = solicitar_acao


def _limpar_pendente() -> None:
    st.session_state[_CHAVE_PENDENTE] = None


def renderizar_cartao(
    on_confirmar: Callable[[str, dict[str, Any]], str],
) -> None:
    """Renderiza o formulario se houver pendente; no-op caso contrario.

    `on_confirmar(tool, args)` recebe os args montados a partir dos
    widgets e devolve o texto que sera acrescentado ao historico como
    mensagem do bot. Erros de Pydantic/HTTP ja vem traduzidos pelo
    orquestrador (orquestrador.executar_acao_confirmada).
    """
    pendente = st.session_state.get(_CHAVE_PENDENTE)
    if pendente is None:
        return

    tool = pendente["tool"]
    args_gemini: dict[str, Any] = pendente.get("args") or {}
    campos = campos_de(tool)

    with st.chat_message("assistant"):
        st.markdown(f"**Confirme a ação:** `{tool}`")
        if not campos:
            st.warning(
                f"Sem formulario definido para `{tool}`; ação descartada."
            )
            _limpar_pendente()
            st.rerun()
            return

        valores = _renderizar_campos(tool, campos, args_gemini)
        col_ok, col_cancel = st.columns(2)
        confirmar = col_ok.button("Confirmar", key=f"btn_confirmar_{tool}")
        cancelar = col_cancel.button("Cancelar", key=f"btn_cancelar_{tool}")

    if confirmar:
        _limpar_pendente()
        resposta = on_confirmar(tool, valores)
        acrescentar_mensagem(st.session_state["historico"], "bot", resposta)
        st.rerun()
    elif cancelar:
        _limpar_pendente()
        acrescentar_mensagem(
            st.session_state["historico"], "bot", "Ação cancelada."
        )
        st.rerun()


# --- Renderizacao dos widgets ---


def _renderizar_campos(
    tool: str, campos: tuple[Campo, ...], args: dict[str, Any]
) -> dict[str, Any]:
    """Itera a spec e monta o dict de args a partir dos widgets."""
    saida: dict[str, Any] = {}
    for campo in campos:
        valor = _renderizar_campo(tool, campo, args.get(campo.nome))
        if valor is not None and valor != "":
            saida[campo.nome] = valor
    return saida


def _renderizar_campo(tool: str, campo: Campo, valor_atual: Any) -> Any:
    """Despacha por widget; devolve valor capturado (ou None se sem opcao)."""
    key = f"form_{tool}_{campo.nome}"

    if campo.widget == "text":
        return st.text_input(
            campo.label,
            value=str(valor_atual or ""),
            key=key,
            help=campo.help or None,
        )
    if campo.widget == "password":
        return st.text_input(
            campo.label,
            value=str(valor_atual or ""),
            key=key,
            type="password",
            help=campo.help or None,
        )
    if campo.widget == "number":
        return _render_number(campo, valor_atual, key)
    if campo.widget == "decimal":
        return _render_decimal(campo, valor_atual, key)
    if campo.widget == "select":
        return _render_select(campo, valor_atual, key)
    if campo.widget == "dropdown":
        return _render_dropdown(campo, valor_atual, key)
    if campo.widget == "itens":
        return _render_itens(tool, campo, valor_atual)
    return None


def _render_number(campo: Campo, valor_atual: Any, key: str) -> int:
    default = (
        int(valor_atual)
        if isinstance(valor_atual, (int, float, str)) and str(valor_atual) != ""
        else (campo.min_value if campo.min_value is not None else 0)
    )
    return st.number_input(
        campo.label,
        value=default,
        min_value=campo.min_value,
        step=1,
        key=key,
        help=campo.help or None,
    )


def _render_decimal(campo: Campo, valor_atual: Any, key: str) -> float:
    default = (
        float(valor_atual)
        if isinstance(valor_atual, (int, float, str)) and str(valor_atual) != ""
        else 0.0
    )
    return st.number_input(
        campo.label,
        value=default,
        min_value=float(campo.min_value) if campo.min_value is not None else None,
        step=0.01,
        format="%.2f",
        key=key,
        help=campo.help or None,
    )


def _render_select(campo: Campo, valor_atual: Any, key: str) -> str:
    opcoes = list(campo.opcoes)
    index = opcoes.index(valor_atual) if valor_atual in opcoes else 0
    return st.selectbox(campo.label, opcoes, index=index, key=key)


def _render_dropdown(campo: Campo, valor_atual: Any, key: str) -> Any:
    """Chama fontes_opcoes e renderiza selectbox. Em falha, mostra aviso."""
    try:
        opcoes = opcoes_para(campo.fonte_dropdown)
    except Exception as e:  # APIError ou outro; deixa o form continuar
        st.warning(f"Não consegui carregar opções de {campo.label}: {e}")
        return valor_atual
    if not opcoes:
        st.info(f"Sem opções disponíveis para {campo.label}.")
        return None
    valores = [v for v, _ in opcoes]
    labels = [l for _, l in opcoes]
    index = valores.index(valor_atual) if valor_atual in valores else 0
    label_escolhido = st.selectbox(campo.label, labels, index=index, key=key)
    return valores[labels.index(label_escolhido)]


def _render_itens(
    tool: str, campo: Campo, valor_atual: Any
) -> list[dict[str, Any]]:
    """Lista dinamica de sub-formularios (criar_pedido_manual.itens).

    Numero de linhas vive em `st.session_state[chave_count]`; botoes
    Adicionar/Remover ajustam e fazem rerun. Cada linha tem keys
    proprios por indice — Streamlit retem o valor entre reruns.
    """
    chave_count = f"form_{tool}_{campo.nome}_count"
    valores_atuais = valor_atual if isinstance(valor_atual, list) else []
    if chave_count not in st.session_state:
        st.session_state[chave_count] = max(1, len(valores_atuais))

    n = st.session_state[chave_count]
    st.markdown(f"**{campo.label}**")
    capturados: list[dict[str, Any]] = []
    for i in range(n):
        st.caption(f"Item {i + 1}")
        base = valores_atuais[i] if i < len(valores_atuais) else {}
        linha: dict[str, Any] = {}
        for sub in campo.itens_campos:
            key_sub = f"form_{tool}_{campo.nome}_{i}_{sub.nome}"
            valor_sub = _renderizar_subcampo(sub, base.get(sub.nome), key_sub)
            if valor_sub is not None and valor_sub != "":
                linha[sub.nome] = valor_sub
        capturados.append(linha)

    col_add, col_rm = st.columns(2)
    if col_add.button("Adicionar item", key=f"btn_add_{tool}_{campo.nome}"):
        st.session_state[chave_count] = n + 1
        st.rerun()
    if n > 1 and col_rm.button(
        "Remover último", key=f"btn_rm_{tool}_{campo.nome}"
    ):
        st.session_state[chave_count] = n - 1
        st.rerun()
    return capturados


def _renderizar_subcampo(sub: Campo, valor_atual: Any, key: str) -> Any:
    """Como _renderizar_campo mas com `key` ja resolvida (linha de itens)."""
    if sub.widget == "dropdown":
        return _render_dropdown(sub, valor_atual, key)
    if sub.widget == "number":
        return _render_number(sub, valor_atual, key)
    if sub.widget == "decimal":
        return _render_decimal(sub, valor_atual, key)
    if sub.widget == "text":
        return st.text_input(sub.label, value=str(valor_atual or ""), key=key)
    if sub.widget == "select":
        return _render_select(sub, valor_atual, key)
    return None


__all__ = [
    "ha_pendente",
    "solicitar_acao",
    "solicitar_confirmacao",  # alias retrocompat
    "renderizar_cartao",
]
