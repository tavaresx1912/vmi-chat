"""Rotas do papel Fornecedor: VMI (RN-03), clientes, status de pedido.

Todas exigem `require_role(UserRole.FORNECEDOR)` e checagem extra de
relacao no service (fornecedor so atualiza estoque/status de pedidos que
envolvem produtos dele).
"""

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.user import User, UserRole
from app.schemas.estoque import EstoqueComStatusRead
from app.schemas.fornecedor import (
    AtualizarEstoqueInput,
    AtualizarStatusPedidoInput,
)
from app.schemas.pedido import PedidoCompraRead
from app.schemas.user import UserRead
from app.services import fornecedor as forn_service

router = APIRouter(prefix="/fornecedor", tags=["fornecedor"])
_fornecedor_only = require_role(UserRole.FORNECEDOR)


@router.patch("/estoque", response_model=EstoqueComStatusRead)
def atualizar_estoque(
    payload: AtualizarEstoqueInput,
    current: User = Depends(_fornecedor_only),
    db: Session = Depends(get_db),
) -> EstoqueComStatusRead:
    """VMI - RN-03: fornecedor define a quantidade em estoque do (produto, usuario)."""
    try:
        return forn_service.atualizar_estoque(
            db,
            fornecedor_user_id=current.id,
            produto_id=payload.produto_id,
            usuario_id=payload.usuario_id,
            nova_quantidade=payload.nova_quantidade,
        )
    except forn_service.FornecedorSemCadastroError:
        raise HTTPException(
            http_status.HTTP_403_FORBIDDEN,
            detail="Fornecedor sem cadastro vinculado",
        )
    except forn_service.NaoSupreEsteProdutoError:
        raise HTTPException(
            http_status.HTTP_403_FORBIDDEN,
            detail="Este fornecedor nao supre o produto informado",
        )
    except forn_service.EstoqueInexistenteError:
        raise HTTPException(
            http_status.HTTP_404_NOT_FOUND,
            detail="Estoque (produto, usuario) nao encontrado",
        )


@router.get("/clientes", response_model=list[UserRead])
def listar_clientes(
    current: User = Depends(_fornecedor_only),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    """Lista usuarios distintos que pediram produtos deste fornecedor."""
    try:
        return forn_service.listar_clientes(db, fornecedor_user_id=current.id)
    except forn_service.FornecedorSemCadastroError:
        raise HTTPException(
            http_status.HTTP_403_FORBIDDEN,
            detail="Fornecedor sem cadastro vinculado",
        )


@router.patch(
    "/pedidos/{pedido_id}/status",
    response_model=PedidoCompraRead,
)
def atualizar_status_pedido(
    pedido_id: int,
    payload: AtualizarStatusPedidoInput,
    current: User = Depends(_fornecedor_only),
    db: Session = Depends(get_db),
) -> PedidoCompraRead:
    """Atualiza status do pedido. Auth: forn deve ter ao menos um item no pedido."""
    try:
        return forn_service.atualizar_status_pedido(
            db,
            fornecedor_user_id=current.id,
            pedido_id=pedido_id,
            novo_status=payload.novo_status,
        )
    except forn_service.FornecedorSemCadastroError:
        raise HTTPException(
            http_status.HTTP_403_FORBIDDEN,
            detail="Fornecedor sem cadastro vinculado",
        )
    except forn_service.PedidoInexistenteError:
        raise HTTPException(
            http_status.HTTP_404_NOT_FOUND,
            detail="Pedido nao encontrado",
        )
    except forn_service.PedidoSemItensDoFornecedorError:
        raise HTTPException(
            http_status.HTTP_403_FORBIDDEN,
            detail="Pedido nao contem itens deste fornecedor",
        )
