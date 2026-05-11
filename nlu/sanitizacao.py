"""Sanitização da entrada do usuário antes do bloco [user] do prompt (RNF-15).

Cobre normalização Unicode (NFKC), remoção de caracteres perigosos
(controle, zero-width, bidi-override, surrogates), colapso de whitespace
em espaço único e limite de tamanho. Lança ValueError em entradas vazias
ou longas demais — o caller (Streamlit) traduz isso em mensagem ao usuário.
"""
import re
import unicodedata

# Limite máximo de caracteres da entrada (RNF-15 do PRD).
LIMITE_CARACTERES = 500

# `\s` cobre espaço, \t, \n, \r, \f, \v e equivalentes Unicode.
_WHITESPACE_RE = re.compile(r"\s+")


def _remover_caracteres_perigosos(texto: str) -> str:
    """Remove caracteres das categorias Unicode Cc, Cf e Cs.

    Mantém qualquer whitespace (`str.isspace()`) para que a etapa seguinte
    o colapse em espaço, em vez de apagá-lo e grudar palavras (ex.:
    "Liste\\rpedidos" precisa virar "Liste pedidos", não "Listepedidos").

    - Cc: control characters (NUL, etc.).
    - Cf: format characters (zero-width, BOM, bidi-override).
    - Cs: surrogate halves (não aparecem em texto Unicode válido).
    """
    return "".join(
        c
        for c in texto
        if c.isspace() or unicodedata.category(c) not in ("Cc", "Cf", "Cs")
    )


def sanitizar_entrada_usuario(texto: str) -> str:
    """Limpa e valida o texto digitado antes de entrar no prompt do Gemini.

    Lança ValueError se a entrada ficar vazia após a limpeza ou exceder
    LIMITE_CARACTERES caracteres. O cálculo de tamanho é feito sobre o
    texto JÁ limpo, para não penalizar quem digitou apenas whitespace
    redundante.
    """
    texto = unicodedata.normalize("NFKC", texto)
    texto = _remover_caracteres_perigosos(texto)
    texto = _WHITESPACE_RE.sub(" ", texto).strip()
    if not texto:
        raise ValueError("Entrada vazia depois da sanitização.")
    if len(texto) > LIMITE_CARACTERES:
        raise ValueError(
            f"Entrada excede o limite de {LIMITE_CARACTERES} caracteres "
            f"(recebido: {len(texto)})."
        )
    return texto
