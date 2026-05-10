"""Rotas de autenticação.

Esta rota não tem lógica de negócio (R-ARQ-02): valida o payload, chama o
service de auth e devolve o token. A regra de "como autenticar" mora em
`app/services/auth.py`.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import authenticate

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Autentica um usuário por e-mail e senha e devolve um JWT.

    Retorna 401 se as credenciais não baterem ou o usuário estiver inativo.
    """
    user = authenticate(db, payload.email, payload.senha)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        role=user.role,
    )
