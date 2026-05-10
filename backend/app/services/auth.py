"""Service de autenticação.

Concentra a regra de "como autenticar um usuário": busca por e-mail,
verifica a senha contra o hash e devolve o User autenticado se tudo bater.
"""
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User
from app.repositories import user as user_repo


def authenticate(db: Session, email: str, senha: str) -> User | None:
    """Autentica um usuário por e-mail e senha em texto puro.

    Retorna o User se as credenciais batem e o usuário está ativo.
    Retorna None caso contrário (a rota traduz None em HTTP 401).
    """
    user = user_repo.get_by_email(db, email)
    if user is None:
        return None
    if not user.ativo:
        return None
    if not verify_password(senha, user.senha_hash):
        return None
    return user
