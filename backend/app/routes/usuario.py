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
from app.schemas.estoque import (
    ConfigurarPontosInput,
    EstoqueComStatusRead,
    EstoqueUrgenteRead,
)
from app.schemas.fornecedor import FornecedorRead
from app.schemas.pedido import (
    PedidoCompraComItensCreate,
    PedidoCompraComItensRead,
    PedidoCompraRead,
    PedidoReposicaoInput,
)
from app.schemas.produto import CadastrarProdutoInput, ProdutoRead
from app.schemas.produto_fornecedor import (
    ProdutoFornecedorOpcaoRead,
    ProdutoFornecedorRead,
)
from app.services import estoque as estoque_service
from app.services import fornecedor as forn_service
from app.services import pedido as pedido_service
from app.services import priorizacao_reposicao as prio_service
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


@router.get(
    "/produtos-fornecedores",
    response_model=list[ProdutoFornecedorOpcaoRead],
)
def listar_produtos_fornecedores(
    current: User = Depends(_usuario_only),
    db: Session = Depends(get_db),
) -> list[ProdutoFornecedorOpcaoRead]:
    """Lista contratos PF enriquecidos para o dropdown de itens do pedido manual."""
    return produto_service.listar_opcoes_produto_fornecedor(db)


# --- fornecedores ---


@router.get(
    "/fornecedores",
    response_model=list[FornecedorRead],
)
def listar_fornecedores_usuario(
    termo: str | None = Query(default=None, max_length=120),
    current: User = Depends(_usuario_only),
    db: Session = Depends(get_db),
) -> list[FornecedorRead]:
    """Lista fornecedores para o usuario popular dropdown em cadastrar_produto.

    Espelha a logica de admin.listar_fornecedores; preferimos rota
    propria do papel para manter a disciplina de prefixos `/admin/*` x
    `/usuario/*` e permitir divergencia futura no shape da resposta.
    """
    return forn_service.list_fornecedores(db, termo=termo)


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


@router.get(
    "/reposicao/urgentes",
    response_model=list[EstoqueUrgenteRead],
)
def listar_reposicao_urgentes(
    current: User = Depends(_usuario_only),
    db: Session = Depends(get_db),
) -> list[EstoqueUrgenteRead]:
    """Fila de reposicao priorizada: itens criticos do mais urgente ao menos.

    Drena um MinHeap por (deficit, produto_id) -> vermelho aparece antes de
    amarelo; dentro de cada faixa, deficit menor (mais negativo) vem primeiro.
    Verdes ficam de fora.
    """
    return prio_service.listar_urgentes(db, usuario_id=current.id)


@router.post(
    "/pedidos/reposicao",
    response_model=PedidoCompraComItensRead,
    status_code=status.HTTP_201_CREATED,
)
def pedido_reposicao(
    payload: PedidoReposicaoInput,
    current: User = Depends(_usuario_only),
    db: Session = Depends(get_db),
) -> PedidoCompraComItensRead:
    """Pedido automatico de reposicao (RN-07).

    So aceita produtos em status Amarelo ou Vermelho. Usa fornecedor
    preferencial (ou o primeiro vinculado) e quantidade calculada pra
    voltar a faixa Verde respeitando minimo do contrato.
    """
    try:
        return pedido_service.criar_pedido_reposicao(
            db,
            usuario_id=current.id,
            produto_id=payload.produto_id,
        )
    except pedido_service.EstoqueNaoConfiguradoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estoque nao configurado para este produto — configure pontos primeiro",
        )
    except pedido_service.StatusVerdeNaoElegivelError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Produto em status verde, sem necessidade de reposicao (RN-07)",
        )
    except pedido_service.ProdutoSemContratoError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto sem fornecedor vinculado",
        )
