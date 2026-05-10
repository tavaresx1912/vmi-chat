"""Model do usuário (User) e enum de papéis (UserRole).

O User representa qualquer pessoa autenticada na plataforma. O campo
'role' distingue Admin, Usuario e Fornecedor (PRD seção 3, RN-04).
"""
from enum import Enum

from sqlalchemy import Boolean, Enum as SqlEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, Enum):
    """Papéis possíveis no sistema, conforme PRD seção 3."""

    ADMIN = "admin"
    USUARIO = "usuario"
    FORNECEDOR = "fornecedor"


class User(Base):
    """Tabela 'users' - representa qualquer pessoa autenticada na plataforma."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    # Email é a chave de login: único e indexado para acelerar a busca por usuário.
    email: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False, index=True
    )
    # A senha sempre é armazenada em forma de hash. O hashing acontece na camada de auth.
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # native_enum=False mantém compatibilidade com SQLite (VARCHAR).
    # create_constraint=True força a CHECK no banco (default do SQLAlchemy 2.x é False).
    # values_callable faz com que o banco armazene os VALORES do enum ('admin') e não
    # os NOMES ('ADMIN'), conforme PRD §8.
    role: Mapped[UserRole] = mapped_column(
        SqlEnum(
            UserRole,
            native_enum=False,
            length=20,
            create_constraint=True,
            name="user_role",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    # RN-01: Admin pode desativar usuários sem apagá-los do banco.
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
