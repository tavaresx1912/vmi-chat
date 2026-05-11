"""Service do PedidoCompra: criacao de pedido manual + listagem por usuario."""
from typing import Any

from sqlalchemy.orm import Session

from app.models.pedido import ItemPedido, OrigemPedido, PedidoCompra, StatusPedido
from app.repositories import pedido as pedido_repo
from app.repositories import produto_fornecedor as pf_repo
from app.schemas.pedido import ItemPedidoInput
from app.services.busca_ordenacao import ordenar_por_campo


class ContratoInexistenteError(Exception):
    """ProdutoFornecedor referenciado no item nao existe."""


class QuantidadeAbaixoDoMinimoError(Exception):
    """Quantidade pedida e menor que qtd_minima_pedido do contrato."""

    def __init__(self, produto_fornecedor_id: int, quantidade: int, minimo: int) -> None:
        super().__init__(produto_fornecedor_id)
        self.produto_fornecedor_id = produto_fornecedor_id
        self.quantidade = quantidade
        self.minimo = minimo


def _para_dict(pedido: PedidoCompra, itens: list[ItemPedido]) -> dict[str, Any]:
    """Monta o dict que mapeia em PedidoCompraComItensRead."""
    return {
        "id": pedido.id,
        "usuario_id": pedido.usuario_id,
        "status": pedido.status,
        "origem": pedido.origem,
        "criado_em": pedido.criado_em,
        "itens": [
            {
                "id": i.id,
                "pedido_id": i.pedido_id,
                "produto_fornecedor_id": i.produto_fornecedor_id,
                "quantidade": i.quantidade,
                "preco_unitario": i.preco_unitario,
            }
            for i in itens
        ],
    }


def criar_pedido_manual(
    db: Session,
    *,
    usuario_id: int,
    itens_input: list[ItemPedidoInput],
) -> dict[str, Any]:
    """Cria PedidoCompra + N ItemPedido em uma transacao atomica.

    Por item: valida que o ProdutoFornecedor existe e que a quantidade
    atende qtd_minima_pedido do contrato; usa preco_contratado como
    snapshot em preco_unitario. Validacao completa antes do INSERT
    para que um item ruim no meio da lista nao deixe pedido orfao.
    """
    pfs = []
    for inp in itens_input:
        pf = pf_repo.get_by_id(db, inp.produto_fornecedor_id)
        if pf is None:
            raise ContratoInexistenteError(inp.produto_fornecedor_id)
        if inp.quantidade < pf.qtd_minima_pedido:
            raise QuantidadeAbaixoDoMinimoError(
                inp.produto_fornecedor_id, inp.quantidade, pf.qtd_minima_pedido
            )
        pfs.append(pf)

    pedido = PedidoCompra(
        usuario_id=usuario_id,
        status=StatusPedido.PENDENTE,
        origem=OrigemPedido.MANUAL,
    )
    db.add(pedido)
    db.flush()

    itens_db: list[ItemPedido] = []
    for inp, pf in zip(itens_input, pfs):
        item = ItemPedido(
            pedido_id=pedido.id,
            produto_fornecedor_id=inp.produto_fornecedor_id,
            quantidade=inp.quantidade,
            preco_unitario=pf.preco_contratado,
        )
        db.add(item)
        itens_db.append(item)

    db.commit()
    db.refresh(pedido)
    for item in itens_db:
        db.refresh(item)

    return _para_dict(pedido, itens_db)


def listar_pedidos_usuario(
    db: Session,
    *,
    usuario_id: int,
    filtro_origem: OrigemPedido | None = None,
) -> list[PedidoCompra]:
    """Lista pedidos do proprio usuario ordenados por criado_em DESC."""
    todos = pedido_repo.list_by_user(db, usuario_id)

    if filtro_origem is not None:
        # Filtro manual (R-ALG-01).
        filtrados: list[PedidoCompra] = []
        for p in todos:
            if p.origem == filtro_origem:
                filtrados.append(p)
        todos = filtrados

    return ordenar_por_campo(todos, "criado_em", decrescente=True)
