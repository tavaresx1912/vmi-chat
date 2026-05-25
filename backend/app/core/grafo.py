"""Grafo nao-direcionado ponderado em adjacency list (estudo de estrutura de dados).

Representacao: dict[node, dict[vizinho, peso]]. Cada aresta {a,b}=p eh
guardada duas vezes (em adj[a][b] e adj[b][a]), trade-off classico de
adjacency list: O(grau) pra listar vizinhos, O(1) pra consultar uma
aresta, mas dobro de memoria das arestas vs lista de pares.
"""
from collections import deque
from collections.abc import Hashable, Iterator
from typing import Generic, TypeVar

N = TypeVar("N", bound=Hashable)


class Grafo(Generic[N]):
    def __init__(self) -> None:
        self._adj: dict[N, dict[N, float]] = {}

    def add_node(self, node: N) -> None:
        if node not in self._adj:
            self._adj[node] = {}

    def add_edge(self, a: N, b: N, peso: float = 1.0) -> None:
        """Cria/atualiza a aresta {a,b} com o peso dado.

        Idempotente: chamadas repetidas sobrescrevem o peso (nao acumulam).
        Para acumular, o caller faz `g.add_edge(a, b, g.peso(a, b) + delta)`.
        """
        self.add_node(a)
        self.add_node(b)
        if a == b:
            # Self-loop nao faz sentido no dominio (fornecedor consigo mesmo).
            return
        self._adj[a][b] = peso
        self._adj[b][a] = peso

    def vizinhos(self, node: N) -> dict[N, float]:
        """Devolve dict {vizinho: peso}. Vazio se node nao existir."""
        return self._adj.get(node, {})

    def peso(self, a: N, b: N) -> float:
        """Peso da aresta {a,b}; 0 se nao existir."""
        return self._adj.get(a, {}).get(b, 0.0)

    def __contains__(self, node: object) -> bool:
        return node in self._adj

    def __iter__(self) -> Iterator[N]:
        return iter(self._adj)

    def __len__(self) -> int:
        return len(self._adj)

    def bfs(self, source: N, max_depth: int = 1) -> list[tuple[N, int, float]]:
        """BFS desde source ate max_depth (exclusive source).

        Retorna lista de (node, depth, peso_aresta_ate_descobridor). Ordenada
        pela ordem de visita (depth crescente; mesma profundidade respeita
        ordem de descoberta -> FIFO da fila).

        Complexidade: O(V + E) no pior caso, limitado pela profundidade.
        """
        if source not in self._adj:
            return []

        visitados: set[N] = {source}
        fila: deque[tuple[N, int]] = deque([(source, 0)])
        resultado: list[tuple[N, int, float]] = []

        while fila:
            atual, profundidade = fila.popleft()
            if profundidade == max_depth:
                continue
            for vizinho, peso in self._adj[atual].items():
                if vizinho in visitados:
                    continue
                visitados.add(vizinho)
                resultado.append((vizinho, profundidade + 1, peso))
                fila.append((vizinho, profundidade + 1))

        return resultado
