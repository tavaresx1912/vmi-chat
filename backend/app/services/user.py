"""Service do User: regras de negocio do CRUD administrativo (RN-01).

A rota apenas valida o payload e delega — toda decisao de negocio (email
unico, soft delete, busca/ordenacao manual) vive aqui.
"""
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories import user as user_repo
from app.schemas.user import UserCreate
from app.services.busca_ordenacao import buscar_por_substring, ordenar_por_campo


class EmailJaCadastradoError(Exception):
    """Tentativa de criar usuario com e-mail ja existente."""


def create_user(db: Session, payload: UserCreate) -> User:
    """Cria um novo usuario com senha hasheada.

    Lanca EmailJaCadastradoError se o e-mail ja existir — a rota traduz
    em HTTP 409.
    """
    if user_repo.get_by_email(db, payload.email) is not None:
        raise EmailJaCadastradoError(payload.email)
    user = User(
        nome=payload.nome,
        email=payload.email,
        senha_hash=hash_password(payload.senha),
        role=payload.role,
        ativo=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(
    db: Session,
    *,
    termo: str | None = None,
    filtro: UserRole | None = None,
) -> list[User]:
    """Lista usuarios aplicando busca/ordenacao em memoria (R-ALG-01/02).

    O repository devolve a lista bruta; a regra do projeto proibe
    .filter / .order_by do ORM para localizacao/ordenacao.
    """
    todos = user_repo.list_all(db)

    # Filtro por papel: loop manual (R-ALG-01 proibe filter/comprehension
    # com predicado para localizar elementos).
    if filtro is not None:
        filtrados: list[User] = []
        for u in todos:
            if u.role == filtro:
                filtrados.append(u)
        todos = filtrados

    if termo:
        todos = buscar_por_substring(todos, "nome", termo)

    return ordenar_por_campo(todos, "nome")


def deactivate_user(db: Session, user_id: int) -> User | None:
    """Marca user.ativo = False (soft delete, RN-01). Idempotente.

    Retorna None se o usuario nao existir — a rota traduz em 404.
    Chamar duas vezes nao falha: simplesmente nao altera o estado se
    ja estiver inativo.
    """
    user = user_repo.get_by_id(db, user_id)
    if user is None:
        return None
    if user.ativo:
        user.ativo = False
        db.commit()
        db.refresh(user)
    return user
