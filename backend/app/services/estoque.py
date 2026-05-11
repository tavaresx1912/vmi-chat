"""Service do Estoque: consulta com semaforo (RN-06) e configuracao de pontos."""
from typing import Any

from sqlalchemy.orm import Session

from app.models.estoque import Estoque
from app.repositories import estoque as estoque_repo
from app.repositories import produto as produto_repo


class ProdutoInexistenteError(Exception):
    """Produto referenciado nao existe no catalogo."""


def calcular_status(estoque: Estoque) -> str:
    """Aplica a regra do semaforo Kanban (RN-06).

    - vermelho: quantidade <= ponto_reposicao (critico)
    - amarelo:  ponto_reposicao < quantidade < ponto_amarelo (atencao)
    - verde:    quantidade >= ponto_amarelo (saudavel)
    """
    if estoque.quantidade <= estoque.ponto_reposicao:
        return "vermelho"
    if estoque.quantidade < estoque.ponto_amarelo:
        return "amarelo"
    return "verde"


def _para_dict(estoque: Estoque) -> dict[str, Any]:
    """Monta o dict que mapeia 1:1 em EstoqueComStatusRead."""
    return {
        "id": estoque.id,
        "produto_id": estoque.produto_id,
        "usuario_id": estoque.usuario_id,
        "quantidade": estoque.quantidade,
        "ponto_reposicao": estoque.ponto_reposicao,
        "ponto_amarelo": estoque.ponto_amarelo,
        "status": calcular_status(estoque),
    }


def consultar_estoque(db: Session, *, usuario_id: int) -> list[dict[str, Any]]:
    """Lista o estoque do usuario com status derivado por linha."""
    return [_para_dict(e) for e in estoque_repo.list_by_user(db, usuario_id)]


def configurar_pontos(
    db: Session,
    *,
    usuario_id: int,
    produto_id: int,
    ponto_reposicao: int,
    ponto_amarelo: int,
) -> dict[str, Any]:
    """Define/atualiza os pontos do semaforo para (produto, usuario).

    Lazy init: se nao existir registro de estoque para esse par, cria com
    quantidade=0. Lanca ProdutoInexistenteError se o produto nao existir.
    """
    if produto_repo.get_by_id(db, produto_id) is None:
        raise ProdutoInexistenteError(produto_id)

    estoque = estoque_repo.get_by_produto_e_user(db, produto_id, usuario_id)
    if estoque is None:
        estoque = Estoque(
            produto_id=produto_id,
            usuario_id=usuario_id,
            quantidade=0,
            ponto_reposicao=ponto_reposicao,
            ponto_amarelo=ponto_amarelo,
        )
        db.add(estoque)
    else:
        estoque.ponto_reposicao = ponto_reposicao
        estoque.ponto_amarelo = ponto_amarelo
    db.commit()
    db.refresh(estoque)
    return _para_dict(estoque)
