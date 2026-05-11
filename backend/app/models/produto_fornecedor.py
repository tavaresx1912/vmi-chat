"""Model do contrato Produto x Fornecedor (ProdutoFornecedor).

Tabela de relação N:N entre Produto e Fornecedor (RN-02). Cada linha
representa um contrato com seus próprios termos: preço, prazo e mínimo
de pedido. O flag 'preferencial' marca o fornecedor padrão da reposição
automática (RN-07).
"""
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProdutoFornecedor(Base):
    """Tabela 'produtos_fornecedores' - contrato N:N entre Produto e Fornecedor."""

    __tablename__ = "produtos_fornecedores"
    __table_args__ = (
        # Um produto não pode ter dois contratos com o mesmo fornecedor.
        UniqueConstraint(
            "produto_id", "fornecedor_id", name="uq_produto_fornecedor"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    produto_id: Mapped[int] = mapped_column(
        ForeignKey("produtos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    fornecedor_id: Mapped[int] = mapped_column(
        ForeignKey("fornecedores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Marca o fornecedor padrão da reposição automática (RN-07). A regra de
    # "no máximo um preferencial por produto" é aplicada na camada de service.
    preferencial: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    # Numeric(10, 2) evita erros de ponto flutuante em valores monetários.
    preco_contratado: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    prazo_entrega_dias: Mapped[int] = mapped_column(Integer, nullable=False)
    qtd_minima_pedido: Mapped[int] = mapped_column(Integer, nullable=False)
