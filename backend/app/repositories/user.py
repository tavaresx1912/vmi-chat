"""Repository do User: acesso direto à tabela 'users'.

Funções aqui apenas leem ou gravam dados; nenhuma regra de negócio
(R-ARQ-01).
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_id(db: Session, user_id: int) -> User | None:
    """Retorna o usuário pelo id, ou None se não existir."""
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    """Retorna o usuário pelo e-mail, ou None se não existir."""
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()


def list_all(db: Session) -> list[User]:
    """Retorna todos os usuários sem filtro nem ordenação no banco.

    Filtros/ordenação são feitos em memória pelos services (R-ALG-01/02).
    """
    stmt = select(User)
    return list(db.execute(stmt).scalars().all())
