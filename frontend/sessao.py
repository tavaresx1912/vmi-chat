"""Estrutura do st.session_state - contrato C7 (DIVISAO §3).

Chaves publicadas (outras camadas consultam):
- jwt (str | None): token JWT devolvido pelo backend apos login.
- role (str | None): papel autenticado, "admin" | "usuario" | "fornecedor".
  Ingrid le este campo para filtrar o catalogo de tools por papel.
- user_id (int | None): id do usuario autenticado.
- historico (list): mensagens da conversa em memoria da sessao (RNF-16,
  sem persistencia entre sessoes).
- pendente_confirmacao (dict | None): acao de escrita aguardando
  confirmacao via cartao (RNF-13); None quando nao ha nada pendente.
"""
from typing import Any


def _defaults() -> dict[str, Any]:
    """Defaults frescos a cada chamada.

    Construir os defaults dentro de uma funcao evita que sessoes diferentes
    compartilhem o mesmo objeto `historico` (lista mutavel).
    """
    return {
        "jwt": None,
        "role": None,
        "user_id": None,
        "historico": [],
        "pendente_confirmacao": None,
    }


def inicializar_sessao(session_state) -> None:
    """Aplica os defaults do C7 ao session_state, idempotentemente.

    Chaves ja existentes nao sao sobrescritas — chamar varias vezes (a
    cada rerun do Streamlit) nao zera dados que o usuario ja preencheu.

    Aceita qualquer objeto dict-like; em runtime recebe st.session_state,
    em teste recebe um dict puro.
    """
    for chave, valor in _defaults().items():
        if chave not in session_state:
            session_state[chave] = valor


def fazer_logout(session_state) -> None:
    """Limpa o session_state completo (logout).

    Usar .clear() em vez de remover chaves uma a uma evita risco de
    deixar lixo de futuras features. A proxima renderizacao chama
    inicializar_sessao(), que repopula os defaults do C7.
    """
    session_state.clear()
