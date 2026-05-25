"""Service que monta o grafo de similaridade de fornecedores e o consulta.

Definicao do grafo:
- Nos: todos os Fornecedores cadastrados.
- Arestas: {Fa, Fb} existe sse Fa e Fb sao vinculados a >= 1 produto em
  comum via ProdutoFornecedor. Peso = quantidade de produtos em comum.

Construcao em O(V + sum_p C(grau(p), 2)) onde p sao os produtos:
agrupamos as PFs por produto e, para cada produto, geramos todos os pares
de fornecedores que o atendem. Esses pares contribuem +1 ao peso da
aresta correspondente.
"""
from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.core.grafo import Grafo
from app.models.fornecedor import Fornecedor
from app.repositories import fornecedor as forn_repo
from app.repositories import produto_fornecedor as pf_repo


def construir_grafo(db: Session) -> tuple[Grafo[int], dict[int, Fornecedor]]:
    """Devolve (grafo de IDs, indice id -> Fornecedor).

    O grafo usa int (fornecedor.id) como no para serialicao trivial e
    chaves leves; o indice acompanha pra hidratar os IDs na resposta.
    """
    fornecedores = forn_repo.list_all(db)
    indice: dict[int, Fornecedor] = {f.id: f for f in fornecedores}

    grafo: Grafo[int] = Grafo()
    for fid in indice:
        grafo.add_node(fid)

    # Agrupa fornecedores por produto: dict[produto_id, list[fornecedor_id]].
    por_produto: dict[int, list[int]] = defaultdict(list)
    for pf in pf_repo.list_all(db):
        por_produto[pf.produto_id].append(pf.fornecedor_id)

    # Para cada produto, todo par (Fa, Fb) compartilha esse produto -> +1 no peso.
    for fids in por_produto.values():
        n = len(fids)
        if n < 2:
            continue
        for i in range(n):
            for j in range(i + 1, n):
                a, b = fids[i], fids[j]
                novo_peso = grafo.peso(a, b) + 1
                grafo.add_edge(a, b, novo_peso)

    return grafo, indice


def fornecedores_similares(
    db: Session, *, fornecedor_id: int, profundidade: int = 2
) -> list[dict[str, Any]]:
    """BFS no grafo a partir do fornecedor dado, ate `profundidade` hops.

    Item de saida:
    - id, nome, cnpj: identificacao do fornecedor vizinho.
    - distancia: hops (1 = vizinho direto; 2 = vizinho de vizinho).
    - peso_aresta_descobridor: peso da aresta que conectou esse no a quem o
      descobriu (mais util na distancia 1 = produtos em comum com a origem;
      em distancias maiores e referencia da ponte que trouxe ele).
    """
    grafo, indice = construir_grafo(db)
    if fornecedor_id not in grafo:
        return []

    vizinhanca = grafo.bfs(fornecedor_id, max_depth=profundidade)
    saida: list[dict[str, Any]] = []
    for node, distancia, peso in vizinhanca:
        forn = indice[node]
        saida.append(
            {
                "id": forn.id,
                "nome": forn.nome,
                "cnpj": forn.cnpj,
                "distancia": distancia,
                "peso_aresta_descobridor": int(peso),
            }
        )
    return saida
