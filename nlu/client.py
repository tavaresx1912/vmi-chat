"""Cliente do Google Gemini.

Expõe um getter que devolve uma instância lazy de `genai.Client`
configurada a partir de nlu.config. O `Client` é cacheado para reutilizar
a configuração da API key entre chamadas.
"""
from functools import lru_cache

from google import genai

from nlu.config import settings


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """Devolve a instância compartilhada do cliente Gemini.

    Lança RuntimeError se GEMINI_API_KEY não estiver definida — falhar
    cedo evita que o erro só apareça lá na frente, dentro do Streamlit.
    """
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não configurada. Defina no .env ou no ambiente."
        )
    return genai.Client(api_key=settings.gemini_api_key)
