"""Rotas administrativas (Admin only, RN-01).

CRUD de usuarios e fornecedores. Todas as rotas protegidas pelo guard
`require_role(UserRole.ADMIN)`. Sem regra de negocio aqui (R-ARQ-02) —
a logica vive nos services correspondentes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.user import UserRole
from app.schemas.fornecedor import FornecedorCreate, FornecedorRead
from app.schemas.user import UserCreate, UserRead
from app.services import fornecedor as forn_service
from app.services import user as user_service

router = APIRouter(prefix="/admin", tags=["admin"])

# Instanciamos uma unica dependencia para reuso em todas as rotas do router.
_admin_only = require_role(UserRole.ADMIN)


# --- /admin/usuarios ---


@router.post(
    "/usuarios",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_admin_only)],
)
def criar_usuario(
    payload: UserCreate,
    db: Session = Depends(get_db),
) -> UserRead:
    """Cria um novo usuario. 409 se o e-mail ja existir."""
    try:
        return user_service.create_user(db, payload)
    except user_service.EmailJaCadastradoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail ja cadastrado",
        )


@router.get(
    "/usuarios",
    response_model=list[UserRead],
    dependencies=[Depends(_admin_only)],
)
def listar_usuarios(
    termo: str | None = Query(default=None, max_length=120),
    filtro: UserRole | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    """Lista usuarios ordenados por nome; busca opcional por nome e papel."""
    return user_service.list_users(db, termo=termo, filtro=filtro)


@router.post(
    "/usuarios/{user_id}/desativar",
    response_model=UserRead,
    dependencies=[Depends(_admin_only)],
)
def desativar_usuario(
    user_id: int,
    db: Session = Depends(get_db),
) -> UserRead:
    """Soft delete do usuario (RN-01). Idempotente; 404 se nao existir."""
    user = user_service.deactivate_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario nao encontrado",
        )
    return user


# --- /admin/fornecedores ---


@router.post(
    "/fornecedores",
    response_model=FornecedorRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_admin_only)],
)
def criar_fornecedor(
    payload: FornecedorCreate,
    db: Session = Depends(get_db),
) -> FornecedorRead:
    """Cria um fornecedor (User+Fornecedor em uma transacao)."""
    try:
        return forn_service.create_fornecedor(db, payload)
    except forn_service.EmailJaCadastradoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-mail ja cadastrado",
        )
    except forn_service.CnpjJaCadastradoError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CNPJ ja cadastrado",
        )


@router.get(
    "/fornecedores",
    response_model=list[FornecedorRead],
    dependencies=[Depends(_admin_only)],
)
def listar_fornecedores(
    termo: str | None = Query(default=None, max_length=120),
    db: Session = Depends(get_db),
) -> list[FornecedorRead]:
    """Lista fornecedores ordenados por nome; busca opcional por nome."""
    return forn_service.list_fornecedores(db, termo=termo)


@router.post(
    "/fornecedores/{fornecedor_id}/desativar",
    response_model=FornecedorRead,
    dependencies=[Depends(_admin_only)],
)
def desativar_fornecedor(
    fornecedor_id: int,
    db: Session = Depends(get_db),
) -> FornecedorRead:
    """Soft delete do fornecedor (RN-01). Idempotente; 404 se nao existir."""
    fornecedor = forn_service.deactivate_fornecedor(db, fornecedor_id)
    if fornecedor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor nao encontrado",
        )
    return fornecedor
