"""Service do Produto: catalogo, busca e cadastro com vinculo a fornecedor."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.produto import Produto
from app.models.produto_fornecedor import ProdutoFornecedor
from app.repositories import fornecedor as forn_repo
from app.repositories import produto as produto_repo
from app.repositories import produto_fornecedor as pf_repo
from app.schemas.produto_fornecedor import ProdutoFornecedorOpcaoRead
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


def listar_opcoes_produto_fornecedor(
    db: Session,
) -> list[ProdutoFornecedorOpcaoRead]:
    """Lista contratos PF enriquecidos com nome do produto e do fornecedor.

    Usado pelo frontend para popular o dropdown de itens em
    criar_pedido_manual sem precisar de chamadas extras por contrato.
    Contratos cujo produto ou fornecedor referenciado nao exista mais
    sao ignorados defensivamente (orfaos nao apareceram no dropdown).
    Ordena por nome do produto (R-ALG-02: insertion sort manual).
    """
    pfs = pf_repo.list_all(db)
    opcoes: list[ProdutoFornecedorOpcaoRead] = []
    for pf in pfs:
        produto = produto_repo.get_by_id(db, pf.produto_id)
        fornecedor = forn_repo.get_by_id(db, pf.fornecedor_id)
        if produto is None or fornecedor is None:
            continue
        opcoes.append(
            ProdutoFornecedorOpcaoRead(
                id=pf.id,
                produto_id=pf.produto_id,
                produto_nome=produto.nome,
                fornecedor_id=pf.fornecedor_id,
                fornecedor_nome=fornecedor.nome,
                preco_contratado=pf.preco_contratado,
                qtd_minima_pedido=pf.qtd_minima_pedido,
            )
        )
    return ordenar_por_campo(opcoes, "produto_nome")
