"""Cliente HTTP do frontend para o backend FastAPI.

Wrapper em torno de httpx que:
- Injeta `Authorization: Bearer <jwt>` automaticamente lendo st.session_state.
  Pode ser desligado com auth=False (caso da tela de login, pre-token).
- Padroniza erro: HTTP nao-2xx vira APIError com `status` + `detail` em
  pt-br pronto para exibir. Formato C3 (`{"detail": "..."}`) e respeitado;
  para 422 (Pydantic ValidationError, que devolve lista de erros) os
  campos `msg` sao concatenados.
- Servidor indisponivel (httpx.RequestError) tambem vira APIError, com
  status=0 para distinguir de erro vindo do backend.
"""
import os
from typing import Any

import httpx
import streamlit as st


_BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
_DEFAULT_TIMEOUT = 10.0


class APIError(Exception):
    """Erro na chamada a API do backend.

    Atributos:
    - status: codigo HTTP da resposta, ou 0 se o servidor estiver fora do ar.
    - detail: mensagem em pt-br pronta para exibir ao usuario.
    """

    def __init__(self, status: int, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail


def _build_headers(auth: bool) -> dict[str, str]:
    """Monta o dict de headers — injeta Bearer se auth=True e ha jwt na sessao."""
    if not auth:
        return {}
    token = st.session_state.get("jwt")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _extrair_detail(resp: httpx.Response) -> str:
    """Le o campo `detail` do formato C3. Fallbacks defensivos."""
    try:
        data = resp.json()
    except ValueError:
        return f"HTTP {resp.status_code}"
    if not isinstance(data, dict):
        return f"HTTP {resp.status_code}"
    detail = data.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        # Pydantic 422 devolve lista de erros; concatena os campos `msg`.
        partes: list[str] = []
        for item in detail:
            if isinstance(item, dict) and "msg" in item:
                partes.append(str(item["msg"]))
        if partes:
            return "; ".join(partes)
    return f"HTTP {resp.status_code}"


def _processar(resp: httpx.Response) -> Any:
    """Converte httpx.Response em valor de retorno OU APIError."""
    if 200 <= resp.status_code < 300:
        if resp.status_code == 204 or not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return resp.text
    raise APIError(resp.status_code, _extrair_detail(resp))


def get(
    path: str,
    *,
    params: dict[str, Any] | None = None,
    auth: bool = True,
    timeout: float = _DEFAULT_TIMEOUT,
) -> Any:
    """GET em `path`. Devolve JSON da resposta ou levanta APIError."""
    try:
        resp = httpx.get(
            f"{_BACKEND_URL}{path}",
            params=params,
            headers=_build_headers(auth),
            timeout=timeout,
        )
    except httpx.RequestError:
        raise APIError(
            0, "Servidor indisponível. Tente novamente em alguns instantes."
        )
    return _processar(resp)


def post(
    path: str,
    *,
    json: Any = None,
    auth: bool = True,
    timeout: float = _DEFAULT_TIMEOUT,
) -> Any:
    """POST em `path` com corpo JSON. Devolve resposta ou levanta APIError."""
    try:
        resp = httpx.post(
            f"{_BACKEND_URL}{path}",
            json=json,
            headers=_build_headers(auth),
            timeout=timeout,
        )
    except httpx.RequestError:
        raise APIError(
            0, "Servidor indisponível. Tente novamente em alguns instantes."
        )
    return _processar(resp)


def request(
    metodo: str,
    path: str,
    *,
    json: Any = None,
    params: dict[str, Any] | None = None,
    auth: bool = True,
    timeout: float = _DEFAULT_TIMEOUT,
) -> Any:
    """Chamada generica por verbo HTTP (cobre PATCH/PUT/DELETE).

    Existe pra atender o orquestrador, que precisa despachar PATCH em
    algumas tools. Para GET/POST simples, prefira get()/post() — sao
    leitura mais direta.
    """
    try:
        resp = httpx.request(
            metodo.upper(),
            f"{_BACKEND_URL}{path}",
            json=json,
            params=params,
            headers=_build_headers(auth),
            timeout=timeout,
        )
    except httpx.RequestError:
        raise APIError(
            0, "Servidor indisponível. Tente novamente em alguns instantes."
        )
    return _processar(resp)
