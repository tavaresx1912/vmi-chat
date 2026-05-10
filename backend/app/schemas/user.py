"""Schemas Pydantic de entrada e saída para o User."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Dados para criar um usuário (RN-01: criação feita pelo Admin)."""

    nome: str = Field(min_length=1, max_length=120)
    email: EmailStr
    # Senha em texto puro - será transformada em hash na camada de service.
    senha: str = Field(min_length=6, max_length=128)
    role: UserRole


class UserRead(BaseModel):
    """Resposta pública de um usuário. Nunca expõe senha nem hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    role: UserRole
    ativo: bool
