"""Estrutura do st.session_state - contrato C7 (DIVISAO §3).

Chaves publicadas (outras camadas consultam):
- jwt (str | None): token JWT devolvido pelo backend apos login.
- role (str | None): papel autenticado, "admin" | "usuario" | "fornecedor".
  Ingrid le este campo para filtrar o catalogo de tools por papel.
- user_id (int | None): id do usuario autenticado.
- historico (list): mensagens da conversa em memoria da sessao (RNF-16,
  sem persistencia entre sessoes).
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
