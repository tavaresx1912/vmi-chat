"""Catalogo de tools de Admin (PRD §11.3, RN-01).

Cada tool expoe dois artefatos:
- DECL_*: dict no formato function declaration do Gemini, pronto pra
  passar ao SDK em GenerativeModel(tools=...).
- *Args: classe Pydantic para validar os argumentos retornados pelo Gemini
  antes do Streamlit chamar o backend (PRD §11.4 passo 2).
"""
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


# Papeis do sistema, espelhados do backend (UserRole) sem import direto
# para preservar a independencia da camada NLU.
TipoPapel = Literal["admin", "usuario", "fornecedor"]
_PAPEIS_VALIDOS = ["admin", "usuario", "fornecedor"]


# --- criar_usuario ---


class CriarUsuarioArgs(BaseModel):
    """Argumentos da tool criar_usuario (RN-01)."""

    nome: str = Field(min_length=1, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=6, max_length=128)
    role: TipoPapel


DECL_CRIAR_USUARIO: dict[str, Any] = {
    "name": "criar_usuario",
    "description": (
        "Cria um novo usuario no sistema (RN-01). Apenas Admin pode chamar."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "nome": {
                "type": "string",
                "description": "Nome completo do usuario.",
            },
            "email": {
                "type": "string",
                "description": "Email unico, usado como login.",
            },
            "senha": {
                "type": "string",
                "description": (
                    "Senha em texto puro; o backend transforma em hash."
                ),
            },
            "role": {
                "type": "string",
                "enum": _PAPEIS_VALIDOS,
                "description": "Papel do novo usuario.",
            },
        },
        "required": ["nome", "email", "senha", "role"],
    },
}


# --- listar_usuarios ---


class ListarUsuariosArgs(BaseModel):
    """Argumentos da tool listar_usuarios.

    `filtro` opcional limita a busca a um papel especifico.
    """

    filtro: TipoPapel | None = None


DECL_LISTAR_USUARIOS: dict[str, Any] = {
    "name": "listar_usuarios",
    "description": (
        "Lista usuarios cadastrados. Opcionalmente filtra por papel. "
        "Apenas Admin pode chamar."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "filtro": {
                "type": "string",
                "enum": _PAPEIS_VALIDOS,
                "description": "Papel para filtrar a lista (opcional).",
            },
        },
    },
}


# --- desativar_usuario ---


class DesativarUsuarioArgs(BaseModel):
    """Argumentos da tool desativar_usuario (RN-01)."""

    usuario_id: int = Field(gt=0)


DECL_DESATIVAR_USUARIO: dict[str, Any] = {
    "name": "desativar_usuario",
    "description": (
        "Desativa um usuario sem apaga-lo (RN-01). Apenas Admin pode chamar."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "usuario_id": {
                "type": "integer",
                "description": "ID numerico do usuario a desativar.",
            },
        },
        "required": ["usuario_id"],
    },
}


# Catalogo agregado, na ordem do PRD §11.3.
TOOLS_ADMIN: list[dict[str, Any]] = [
    DECL_CRIAR_USUARIO,
    DECL_LISTAR_USUARIOS,
    DECL_DESATIVAR_USUARIO,
]

# Mapa nome -> classe Pydantic, para validacao dos argumentos retornados
# pelo Gemini antes do Streamlit chamar o backend.
SCHEMAS_ARGS_ADMIN: dict[str, type[BaseModel]] = {
    "criar_usuario": CriarUsuarioArgs,
    "listar_usuarios": ListarUsuariosArgs,
    "desativar_usuario": DesativarUsuarioArgs,
}
