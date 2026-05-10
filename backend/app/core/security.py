"""Funções utilitárias de segurança: hash de senha e geração/validação de JWT.

Este módulo é puramente técnico — não conhece o domínio do VMI. As regras
de negócio (qual usuário pode logar, etc.) ficam na camada de Service.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from app.config import settings


# bcrypt impõe um limite de 72 bytes para a senha. Truncamos sempre antes do hash
# para manter a senha utilizável e evitar ValueError em entradas longas.
_BCRYPT_MAX_BYTES = 72


def hash_password(plain_password: str) -> str:
    """Gera o hash bcrypt de uma senha em texto puro."""
    pw_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verifica se uma senha em texto puro corresponde ao hash armazenado."""
    pw_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(pw_bytes, password_hash.encode("utf-8"))


def create_access_token(subject: str, role: str) -> str:
    """Cria um JWT com claims 'sub' (id do usuário), 'role' e 'exp'.

    O JWT é assinado simetricamente com a chave secreta da aplicação. O
    'sub' é sempre uma string (claim padrão do JWT).
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decodifica e valida o JWT.

    Levanta JWTError se o token estiver expirado, mal formado ou com
    assinatura inválida. A camada de dependência traduz isso em HTTP 401.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
