"""Service do Fornecedor: CRUD administrativo (RN-01) e operacoes VMI (RN-03).

Criar fornecedor envolve User (role=fornecedor) + Fornecedor numa unica
transacao — se qualquer um falhar, rollback completo. As operacoes VMI
(atualizar estoque, listar clientes, atualizar status de pedido) exigem
que o User logado tenha um record Fornecedor vinculado e checam a
relacao com produto/pedido alvo.
"""
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.fornecedor import Fornecedor
from app.models.pedido import PedidoCompra, StatusPedido
from app.models.user import User, UserRole
from app.repositories import estoque as estoque_repo
from app.repositories import fornecedor as forn_repo
from app.repositories import pedido as pedido_repo
from app.repositories import produto_fornecedor as pf_repo
from app.repositories import user as user_repo
from app.schemas.fornecedor import FornecedorCreate
from app.services import estoque as estoque_service
from app.services.busca_ordenacao import buscar_por_substring, ordenar_por_campo


class EmailJaCadastradoError(Exception):
    """E-mail ja em uso por outro usuario."""


class CnpjJaCadastradoError(Exception):
    """CNPJ ja em uso por outro fornecedor."""


class FornecedorSemCadastroError(Exception):
    """User com role=fornecedor mas sem record Fornecedor vinculado."""


class NaoSupreEsteProdutoError(Exception):
    """O fornecedor nao tem contrato (ProdutoFornecedor) para este produto."""


class EstoqueInexistenteError(Exception):
    """Nao existe registro de Estoque para (produto, usuario)."""


class PedidoInexistenteError(Exception):
    """Pedido referenciado nao existe."""


class PedidoSemItensDoFornecedorError(Exception):
    """O pedido nao contem itens supridos por este fornecedor."""


def create_fornecedor(db: Session, payload: FornecedorCreate) -> Fornecedor:
    """Cria User (role=fornecedor) + Fornecedor numa transacao atomica.

    Lanca EmailJaCadastradoError ou CnpjJaCadastradoError em duplicidade
    detectada antes do insert. IntegrityError do banco (corrida) aborta
    a transacao com rollback e propaga.
    """
    if user_repo.get_by_email(db, payload.email) is not None:
        raise EmailJaCadastradoError(payload.email)
    if forn_repo.get_by_cnpj(db, payload.cnpj) is not None:
        raise CnpjJaCadastradoError(payload.cnpj)

    user = User(
        nome=payload.nome,
        email=payload.email,
        senha_hash=hash_password(payload.senha),
        role=UserRole.FORNECEDOR,
        ativo=True,
    )
    db.add(user)
    try:
        # flush atribui user.id sem commitar — necessario para criar
        # o Fornecedor referenciando-o na mesma transacao.
        db.flush()
        fornecedor = Fornecedor(
            user_id=user.id,
            nome=payload.nome,
            cnpj=payload.cnpj,
        )
        db.add(fornecedor)
        db.commit()
        db.refresh(fornecedor)
    except IntegrityError:
        db.rollback()
        raise
    return fornecedor


def list_fornecedores(
    db: Session,
    *,
    termo: str | None = None,
) -> list[Fornecedor]:
    """Lista fornecedores com busca/ordenacao manual (R-ALG-01/02)."""
    todos = forn_repo.list_all(db)
    if termo:
        todos = buscar_por_substring(todos, "nome", termo)
    return ordenar_por_campo(todos, "nome")


def deactivate_fornecedor(db: Session, fornecedor_id: int) -> Fornecedor | None:
    """Desativa o User vinculado ao Fornecedor (soft delete). Idempotente.

    O Fornecedor em si permanece — desativacao acontece no User.ativo
    (decisao H do plano: nao adicionar coluna ativa em Fornecedor).
    Retorna None se o Fornecedor nao existir.
    """
    fornecedor = forn_repo.get_by_id(db, fornecedor_id)
    if fornecedor is None:
        return None
    user = user_repo.get_by_id(db, fornecedor.user_id)
    if user is not None and user.ativo:
        user.ativo = False
        db.commit()
        db.refresh(fornecedor)
    return fornecedor


# --- operacoes VMI (RN-03) ---


def _fornecedor_do_user(db: Session, user_id: int) -> Fornecedor:
    """Helper: resolve User -> Fornecedor record (1:1). Levanta se nao houver."""
    forn = forn_repo.get_by_user_id(db, user_id)
    if forn is None:
        raise FornecedorSemCadastroError(user_id)
    return forn


def atualizar_estoque(
    db: Session,
    *,
    fornecedor_user_id: int,
    produto_id: int,
    usuario_id: int,
    nova_quantidade: int,
) -> dict[str, Any]:
    """Define Estoque(produto, usuario).quantidade. RN-03 (VMI).

    Checagens: (1) user logado tem Fornecedor vinculado, (2) fornecedor
    supre o produto (existe ProdutoFornecedor), (3) ja existe Estoque
    para esse (produto, usuario) — o estoque foi inicializado pelo usuario
    via `configurar_pontos`, nao pelo fornecedor.
    """
    forn = _fornecedor_do_user(db, fornecedor_user_id)

    if pf_repo.get_by_produto_e_fornecedor(db, produto_id, forn.id) is None:
        raise NaoSupreEsteProdutoError(produto_id)

    estoque = estoque_repo.get_by_produto_e_user(db, produto_id, usuario_id)
    if estoque is None:
        raise EstoqueInexistenteError((produto_id, usuario_id))

    estoque.quantidade = nova_quantidade
    db.commit()
    db.refresh(estoque)
    return {
        "id": estoque.id,
        "produto_id": estoque.produto_id,
        "usuario_id": estoque.usuario_id,
        "quantidade": estoque.quantidade,
        "ponto_reposicao": estoque.ponto_reposicao,
        "ponto_amarelo": estoque.ponto_amarelo,
        "status": estoque_service.calcular_status(estoque),
    }


def listar_clientes(db: Session, *, fornecedor_user_id: int) -> list[User]:
    """Usuarios distintos que pediram produtos deste fornecedor."""
    forn = _fornecedor_do_user(db, fornecedor_user_id)
    return pedido_repo.list_clientes_do_fornecedor(db, forn.id)


def atualizar_status_pedido(
    db: Session,
    *,
    fornecedor_user_id: int,
    pedido_id: int,
    novo_status: StatusPedido,
) -> PedidoCompra:
    """Atualiza status do pedido. Auth: fornecedor deve ter item no pedido.

    Sem validacao de maquina de estados — PRD nao define transicoes
    invalidas; qualquer valor do enum e aceito.
    """
    forn = _fornecedor_do_user(db, fornecedor_user_id)

    pedido = pedido_repo.get_by_id(db, pedido_id)
    if pedido is None:
        raise PedidoInexistenteError(pedido_id)

    if not pedido_repo.fornecedor_tem_itens_no_pedido(db, forn.id, pedido_id):
        raise PedidoSemItensDoFornecedorError(pedido_id)

    pedido.status = novo_status
    db.commit()
    db.refresh(pedido)
    return pedido
