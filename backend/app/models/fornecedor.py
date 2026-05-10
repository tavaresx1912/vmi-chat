"""Model do fornecedor (Fornecedor).

Cada Fornecedor é vinculado a um User com role='fornecedor' e mantém
seus próprios dados de identificação (nome fantasia, CNPJ).
"""
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import User


class Fornecedor(Base):
    """Tabela 'fornecedores' - dados de identificação do fornecedor."""

    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Vínculo 1:1 com User. unique=True garante que cada User tem no máximo um Fornecedor.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    # CNPJ em formato puro (apenas 14 dígitos). A formatação visual fica no frontend.
    cnpj: Mapped[str] = mapped_column(
        String(14), unique=True, nullable=False, index=True
    )

    # Relacionamento ORM: facilita acessar o User a partir do Fornecedor (fornecedor.user).
    user: Mapped[User] = relationship("User")
