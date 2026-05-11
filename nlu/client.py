"""Cliente do Google Gemini.

Expõe um getter que devolve uma instância lazy de GenerativeModel
configurada a partir de nlu.config. A configuração global da SDK
(api_key) ocorre apenas no primeiro acesso.
"""
from functools import lru_cache

import google.generativeai as genai

from nlu.config import settings


@lru_cache(maxsize=1)
def get_client() -> genai.GenerativeModel:
    """Devolve a instância compartilhada do cliente Gemini.

    Lança RuntimeError se GEMINI_API_KEY não estiver definida — falhar
    cedo evita que o erro só apareça lá na frente, dentro do Streamlit.
    """
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não configurada. Defina no .env ou no ambiente."
        )
    genai.configure(api_key=settings.gemini_api_key)
    return genai.GenerativeModel(settings.gemini_model)
