"""Service do Produto: catalogo, busca e cadastro com vinculo a fornecedor."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.produto import Produto
from app.models.produto_fornecedor import ProdutoFornecedor
from app.repositories import fornecedor as forn_repo
from app.repositories import produto as produto_repo
from app.services.busca_ordenacao import buscar_por_substring, ordenar_por_campo


class FornecedorInexistenteError(Exception):
    """Fornecedor referenciado no cadastro nao existe."""


# Default acordado para o gap PRD §11.3 (tool cadastrar_produto nao expoe
# prazo_entrega_dias, mas o model ProdutoFornecedor exige). 7 dias e um
# valor neutro; futura branch pode expor o campo no tool/endpoint.
_PRAZO_ENTREGA_DEFAULT = 7


def cadastrar_produto_com_vinculo(
    db: Session,
    *,
    nome: str,
    categoria: str,
    descricao: str | None,
    fornecedor_id: int,
    preco_contratado: Decimal,
    qtd_minima_pedido: int,
) -> ProdutoFornecedor:
    """Cria Produto novo + ProdutoFornecedor numa transacao (RN-02).

    Lanca FornecedorInexistenteError se o fornecedor nao existir.
    """
    if forn_repo.get_by_id(db, fornecedor_id) is None:
        raise FornecedorInexistenteError(fornecedor_id)

    produto = Produto(nome=nome, categoria=categoria, descricao=descricao)
    db.add(produto)
    db.flush()  # garante produto.id sem commitar
    pf = ProdutoFornecedor(
        produto_id=produto.id,
        fornecedor_id=fornecedor_id,
        preco_contratado=preco_contratado,
        qtd_minima_pedido=qtd_minima_pedido,
        prazo_entrega_dias=_PRAZO_ENTREGA_DEFAULT,
        preferencial=False,
    )
    db.add(pf)
    db.commit()
    db.refresh(pf)
    return pf


def buscar_produtos(
    db: Session,
    *,
    termo: str | None = None,
    categoria: str | None = None,
) -> list[Produto]:
    """Busca produtos com filtros opcionais.

    R-ALG-01/02: busca por substring no nome (linear) e filtro por
    categoria (loop manual); ordena por nome (insertion sort).
    """
    todos = produto_repo.list_all(db)

    if categoria:
        # Filtro por categoria exata via loop manual (R-ALG-01 proibe
        # filter()/comprehension com predicado para localizar elementos).
        filtrados: list[Produto] = []
        for p in todos:
            if p.categoria == categoria:
                filtrados.append(p)
        todos = filtrados

    if termo:
        todos = buscar_por_substring(todos, "nome", termo)

    return ordenar_por_campo(todos, "nome")
