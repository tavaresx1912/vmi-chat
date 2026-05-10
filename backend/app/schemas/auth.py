"""Schemas Pydantic do fluxo de autenticação."""
from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Payload do POST /auth/login."""

    email: EmailStr
    senha: str = Field(min_length=6, max_length=128)


class TokenResponse(BaseModel):
    """Resposta do login.

    Inclui access_token (JWT) e dados auxiliares (user_id, role) para que
    o frontend não precise decodificar o token só para saber o papel.
    """

    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: UserRole
