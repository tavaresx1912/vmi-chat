"""Model do estoque (Estoque).

Cada Estoque representa o saldo de um Produto sob a gestão de um Usuário
(VMI - RN-03). Os pontos de reposição alimentam o semáforo Kanban (RN-06).
"""
from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Estoque(Base):
    """Tabela 'estoques' - saldo por (Produto, Usuário)."""

    __tablename__ = "estoques"
    __table_args__ = (
        # Cada Usuário tem no máximo um registro de estoque por Produto.
        UniqueConstraint(
            "produto_id", "usuario_id", name="uq_estoque_produto_usuario"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantidade: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Faixas do semáforo Kanban (RN-06). O invariante
    # ponto_amarelo > ponto_reposicao é validado no schema Pydantic na entrada
    # e reforçado na camada de service.
    ponto_reposicao: Mapped[int] = mapped_column(Integer, nullable=False)
    ponto_amarelo: Mapped[int] = mapped_column(Integer, nullable=False)
