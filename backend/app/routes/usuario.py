"""Rotas do papel Usuario: catalogo, estoque, pontos de reposicao e pedidos.

Todas as rotas exigem role guard `require_role(UserRole.USUARIO)`. Sem
regra de negocio aqui (R-ARQ-02) — services correspondentes carregam a
logica.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_role
from app.models.pedido import OrigemPedido
from app.models.user import User, UserRole
from app.schemas.estoque import ConfigurarPontosInput, EstoqueComStatusRead
from app.schemas.pedido import (
    PedidoCompraComItensCreate,
    PedidoCompraComItensRead,
    PedidoCompraRead,
)
from app.schemas.produto import CadastrarProdutoInput, ProdutoRead
from app.schemas.produto_fornecedor import ProdutoFornecedorRead
from app.services import estoque as estoque_service
from app.services import pedido as pedido_service
from app.services import produto as produto_service

router = APIRouter(prefix="/usuario", tags=["usuario"])
_usuario_only = require_role(UserRole.USUARIO)


# --- produtos ---


@router.post(
    "/produtos",
    response_model=ProdutoFornecedorRead,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_produto(
    payload: CadastrarProdutoInput,
    current: User = Depends(_usuario_only),
    db: Session = Depends(get_db),
) -> ProdutoFornecedorRead:
    """Cria um Produto novo + ProdutoFornecedor (RN-02)."""
    try:
        return produto_service.cadastrar_produto_com_vinculo(
            db,
            nome=payload.nome,
            categoria=payload.categoria,
            descricao=payload.descricao,
            fornecedor_id=payload.fornecedor_id,
            preco_contratado=payload.preco_contratado,
            qtd_minima_pedido=payload.qtd_minima_pedido,
        )
    except produto_service.FornecedorInexistenteError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fornecedor nao encontrado",
        )


@router.get(
    "/produtos",
    response_model=list[ProdutoRead],
)
def buscar_produtos(
    termo: str | None = Query(default=None, max_length=120),
    categoria: str | None = Query(default=None, max_length=60),
    current: User = Depends(_usuario_only),
    db: Session = Depends(get_db),
) -> list[ProdutoRead]:
    """Lista o catalogo com busca/ordenacao manual (R-ALG-01/02)."""
    return produto_service.buscar_produtos(db, termo=termo, categoria=categoria)


# --- estoque ---


@router.get(
    "/estoque",
    response_model=list[EstoqueComStatusRead],
)
def consultar_estoque(
    current: User = Depends(_usuario_only),
    db: Session = Depends(get_db),
) -> list[EstoqueComStatusRead]:
    """Lista o proprio estoque com status do semaforo (RN-06)."""
    return estoque_service.consultar_estoque(db, usuario_id=current.id)


@router.patch(
    "/estoque/{produto_id}/pontos",
    response_model=EstoqueComStatusRead,
)
def configurar_pontos_estoque(
    produto_id: int,
    payload: ConfigurarPontosInput,
    current: User = Depends(_usuario_only),
    db: Session = Depends(get_db),
) -> EstoqueComStatusRead:
    """Define os pontos de reposicao para um produto (RN-06).

    Cria o registro de estoque com quantidade=0 se ainda nao existir.
    """
    try:
        return estoque_service.configurar_pontos(
            db,
            usuario_id=current.id,
            produto_id=produto_id,
            ponto_reposicao=payload.ponto_reposicao,
            ponto_amarelo=payload.ponto_amarelo,
        )
    except estoque_service.ProdutoInexistenteError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto nao encontrado",
        )


# --- pedidos ---


@router.post(
    "/pedidos",
    response_model=PedidoCompraComItensRead,
    status_code=status.HTTP_201_CREATED,
)
def criar_pedido_manual(
    payload: PedidoCompraComItensCreate,
    current: User = Depends(_usuario_only),
    db: Session = Depends(get_db),
) -> PedidoCompraComItensRead:
    """Cria um pedido manual com seus itens em uma transacao."""
    try:
        return pedido_service.criar_pedido_manual(
            db,
            usuario_id=current.id,
            itens_input=payload.itens,
        )
    except pedido_service.ContratoInexistenteError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contrato ProdutoFornecedor {e.args[0]} nao encontrado",
        )
    except pedido_service.QuantidadeAbaixoDoMinimoError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Quantidade {e.quantidade} abaixo do minimo {e.minimo} "
                f"no contrato {e.produto_fornecedor_id}"
            ),
        )


@router.get(
    "/pedidos",
    response_model=list[PedidoCompraRead],
)
def listar_pedidos(
    filtro: OrigemPedido | None = Query(default=None),
    current: User = Depends(_usuario_only),
    db: Session = Depends(get_db),
) -> list[PedidoCompraRead]:
    """Lista os pedidos do proprio usuario, mais recentes primeiro."""
    return pedido_service.listar_pedidos_usuario(
        db, usuario_id=current.id, filtro_origem=filtro
    )
