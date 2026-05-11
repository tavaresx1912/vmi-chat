"""Algoritmos manuais de busca e ordenacao reutilizaveis (R-ALG-01/02).

Estas funcoes evitam as primitivas embutidas de busca/ordenacao do Python
e do ORM (sorted, list.sort, filter, in, list.index, order_by, etc.). A
regra do projeto exige que o algoritmo seja implementado a mao e a
escolha justificada.
"""
from typing import Any


def _contem_substring(texto: str, padrao: str) -> bool:
    """Verifica se `padrao` aparece em `texto` via varredura linear.

    Substitui o operador `in` (proibido por R-ALG-01 quando usado para
    localizar elementos). Algoritmo: janela deslizante ingenua, O(n*m).
    Suficiente para nomes e categorias curtas de produtos do dominio.
    """
    if not padrao:
        return True
    n, m = len(texto), len(padrao)
    if m > n:
        return False
    for i in range(n - m + 1):
        if texto[i : i + m] == padrao:
            return True
    return False


def buscar_por_substring(
    itens: list[Any],
    campo: str,
    termo: str,
    *,
    ignore_case: bool = True,
) -> list[Any]:
    """Busca LINEAR: retorna itens cujo `campo` contem `termo` como substring.

    R-ALG-01: busca linear porque (a) a colecao nao esta ordenada pelo
    campo de busca (cadastro entra por id, nao por nome/categoria), e (b)
    a comparacao e por substring, que nao admite busca binaria. Itens
    cujo `campo` e None sao ignorados. A ordem original da lista de
    entrada e preservada no resultado.
    """
    termo_norm = termo.lower() if ignore_case else termo
    resultado: list[Any] = []
    for item in itens:
        valor = getattr(item, campo)
        if valor is None:
            continue
        valor_str = str(valor)
        if ignore_case:
            valor_str = valor_str.lower()
        if _contem_substring(valor_str, termo_norm):
            resultado.append(item)
    return resultado


def ordenar_por_campo(
    itens: list[Any],
    campo: str,
    *,
    decrescente: bool = False,
) -> list[Any]:
    """Ordena `itens` por `getattr(item, campo)` usando INSERTION SORT.

    R-ALG-02: insertion sort foi escolhido porque (a) e simples de
    explicar e validar academicamente, (b) e O(n) em listas ja quase
    ordenadas (caso comum quando se reordena apos pequenos cadastros), e
    (c) os tamanhos esperados (dezenas de produtos/pedidos por usuario)
    tornam o pior caso O(n^2) aceitavel. Para listas > 100, vale uma
    branch futura com merge sort.

    Estavel: itens com mesma chave preservam a ordem relativa de entrada.
    Nao muta a lista original — retorna uma copia rasa ordenada. Itens
    cujo campo seja None nao sao tratados especialmente; passar campos
    nullable nesta funcao pode levantar TypeError na comparacao.
    """
    resultado = list(itens)
    n = len(resultado)
    for i in range(1, n):
        atual = resultado[i]
        chave_atual = getattr(atual, campo)
        j = i - 1
        # Desloca para a direita todos os elementos "fora de lugar" em
        # relacao a `atual`, ate encontrar a posicao correta de insercao.
        while j >= 0:
            chave_j = getattr(resultado[j], campo)
            if decrescente:
                fora_de_lugar = chave_j < chave_atual
            else:
                fora_de_lugar = chave_j > chave_atual
            if not fora_de_lugar:
                break
            resultado[j + 1] = resultado[j]
            j -= 1
        resultado[j + 1] = atual
    return resultado
