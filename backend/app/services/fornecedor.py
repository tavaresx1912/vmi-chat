"""Service do Fornecedor: regras de negocio do CRUD administrativo (RN-01).

Criar fornecedor envolve User (role=fornecedor) + Fornecedor numa unica
transacao — se qualquer um falhar, rollback completo.
"""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.fornecedor import Fornecedor
from app.models.user import User, UserRole
from app.repositories import fornecedor as forn_repo
from app.repositories import user as user_repo
from app.schemas.fornecedor import FornecedorCreate
from app.services.busca_ordenacao import buscar_por_substring, ordenar_por_campo


class EmailJaCadastradoError(Exception):
    """E-mail ja em uso por outro usuario."""


class CnpjJaCadastradoError(Exception):
    """CNPJ ja em uso por outro fornecedor."""


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
