"""Dependências do FastAPI compartilhadas: autenticação e role guard.

São funções `Depends`-compatíveis usadas em várias rotas. A separação dos
guards aqui evita duplicação e centraliza a regra de "como saber quem é o
usuário corrente".
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User, UserRole
from app.repositories import user as user_repo


# Esquema HTTP Bearer; o Swagger UI exibe um botão "Authorize" automaticamente.
bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decodifica o JWT do header Authorization e devolve o User correspondente.

    Levanta 401 se o token for inválido ou expirado, ou se o usuário não
    existir mais ou estiver inativo (RN-01).
    """
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais invalidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise invalid

    sub = payload.get("sub")
    if sub is None:
        raise invalid

    user = user_repo.get_by_id(db, int(sub))
    if user is None or not user.ativo:
        raise invalid
    return user


def require_role(*allowed_roles: UserRole):
    """Cria uma dependência que aceita apenas usuários com um dos papéis listados.

    Uso típico em uma rota:
        current = Depends(require_role(UserRole.ADMIN))
    Outros papéis recebem 403 (RNF-07).
    """
    allowed = tuple(allowed_roles)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissao negada para este papel",
            )
        return current_user

    return dependency
