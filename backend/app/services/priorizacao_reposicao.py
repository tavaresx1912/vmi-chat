"""Service que prioriza reposicao usando MinHeap (estudo de estrutura de dados).

Decisao de ordenacao:
- Itens em status 'verde' nao entram (nao precisam reposicao - RN-06).
- Chave de urgencia = quantidade - ponto_reposicao (deficit).
  - vermelho -> deficit <= 0 (mais negativo = mais urgente).
  - amarelo  -> deficit  > 0 (menor positivo = mais urgente).
- Empate na chave: desempata por produto_id (estabilidade do heap ja garante
  FIFO entre chaves iguais; aqui a chave embute produto_id como tiebreaker).

Por que heap e nao apenas sorted()?
- O caso de uso natural e drenar a fila enquanto pedidos sao despachados.
  pop() devolve sempre o mais critico em O(log n), enquanto inserir novos
  itens criticos (ex.: consumo intermediario) custa O(log n). Em sorted()
  cada insercao custaria O(n log n).
"""
from typing import Any

from sqlalchemy.orm import Session

from app.core.heap import MinHeap
from app.models.estoque import Estoque
from app.repositories import estoque as estoque_repo
from app.services.estoque import calcular_status


def _chave_urgencia(estoque: Estoque) -> tuple[int, int]:
    """Chave do heap: (deficit, produto_id).

    deficit < 0 -> abaixo do ponto de reposicao (vermelho).
    deficit > 0 -> entre ponto_reposicao e ponto_amarelo (amarelo).
    produto_id como tiebreaker para resultado determinista entre runs.
    """
    deficit = estoque.quantidade - estoque.ponto_reposicao
    return (deficit, estoque.produto_id)


def listar_urgentes(db: Session, *, usuario_id: int) -> list[dict[str, Any]]:
    """Devolve estoques que precisam reposicao, do mais urgente ao menos.

    Carrega todos os estoques do usuario, filtra os criticos (amarelo+vermelho)
    via calcular_status (RN-06), insere num MinHeap pela chave de urgencia e
    drena na ordem. Verdes ficam fora.
    """
    heap: MinHeap[Estoque] = MinHeap(key=_chave_urgencia)

    for estoque in estoque_repo.list_by_user(db, usuario_id):
        status = calcular_status(estoque)
        if status == "verde":
            continue
        heap.push(estoque)

    resultado: list[dict[str, Any]] = []
    while heap:
        estoque = heap.pop()
        resultado.append(
            {
                "id": estoque.id,
                "produto_id": estoque.produto_id,
                "usuario_id": estoque.usuario_id,
                "quantidade": estoque.quantidade,
                "ponto_reposicao": estoque.ponto_reposicao,
                "ponto_amarelo": estoque.ponto_amarelo,
                "status": calcular_status(estoque),
                "deficit": estoque.quantidade - estoque.ponto_reposicao,
            }
        )
    return resultado
