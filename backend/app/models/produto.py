"""Model do produto (Produto).

Conforme PRD §8, o Produto é a entidade central de catálogo. Não tem
vínculo direto com Fornecedor — o relacionamento é N:N via
ProdutoFornecedor (tabela de contrato, RN-02).
"""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Produto(Base):
    """Tabela 'produtos' - catálogo de itens disponíveis no sistema."""

    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    # Descrição livre, opcional. Renderizada na listagem do catálogo.
    descricao: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Categoria livre por enquanto. Indexada porque o catálogo será filtrado por ela
    # (R-ALG-01 ainda vai rodar busca manual, mas o índice acelera filtros exatos).
    categoria: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
