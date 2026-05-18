"""MinHeap binario implementado na mao (estudo de estrutura de dados).

Espelha a API do heapq da stdlib, mas explicito: push/pop em O(log n) via
sift-up/sift-down; peek em O(1); estavel por contador monotonico interno
que desempata pela ordem de insercao.
"""
from collections.abc import Callable
from itertools import count
from typing import Generic, TypeVar

T = TypeVar("T")


class MinHeap(Generic[T]):
    """Heap binario minimo sobre um array dinamico.

    Cada item e armazenado como (chave, contador, item):
    - 'chave' (resultado do key callback) define a ordem do heap;
    - 'contador' monotonico garante FIFO entre chaves iguais (estabilidade);
    - 'item' e o objeto original, devolvido em pop()/peek().

    Filhos do indice i sao 2i+1 e 2i+2; pai de i e (i-1)//2.
    """

    def __init__(self, key: Callable[[T], object] | None = None) -> None:
        self._items: list[tuple[object, int, T]] = []
        self._key = key if key is not None else (lambda x: x)
        self._counter = count()

    def __len__(self) -> int:
        return len(self._items)

    def __bool__(self) -> bool:
        return bool(self._items)

    def push(self, item: T) -> None:
        entry = (self._key(item), next(self._counter), item)
        self._items.append(entry)
        self._sift_up(len(self._items) - 1)

    def pop(self) -> T:
        if not self._items:
            raise IndexError("pop em MinHeap vazio")
        topo = self._items[0]
        ultimo = self._items.pop()
        if self._items:
            self._items[0] = ultimo
            self._sift_down(0)
        return topo[2]

    def peek(self) -> T:
        if not self._items:
            raise IndexError("peek em MinHeap vazio")
        return self._items[0][2]

    def _sift_up(self, idx: int) -> None:
        while idx > 0:
            pai = (idx - 1) // 2
            if self._items[idx] < self._items[pai]:
                self._items[idx], self._items[pai] = self._items[pai], self._items[idx]
                idx = pai
            else:
                return

    def _sift_down(self, idx: int) -> None:
        n = len(self._items)
        while True:
            esq = 2 * idx + 1
            dir_ = 2 * idx + 2
            menor = idx
            if esq < n and self._items[esq] < self._items[menor]:
                menor = esq
            if dir_ < n and self._items[dir_] < self._items[menor]:
                menor = dir_
            if menor == idx:
                return
            self._items[idx], self._items[menor] = self._items[menor], self._items[idx]
            idx = menor
