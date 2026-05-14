"""Configurações da camada NLU (chat com Google Gemini).

Lidas via Pydantic Settings a partir do .env ou do ambiente do processo.
Os defaults só servem para desenvolvimento local — em execução real, a
chave de API tem de vir do ambiente.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Ancoramos o .env na raiz do repo (pai de nlu/) para que o carregamento
# não dependa do CWD de quem importa este módulo (backend, frontend, etc.).
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class NLUSettings(BaseSettings):
    """Conjunto de configurações da camada NLU."""

    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    # Chave de API do Google Gemini. Obrigatória em execução real.
    gemini_api_key: str = ""

    # Identificador do modelo Gemini usado pelo cliente. Flash 2.0 cobre
    # function calling e tem latência adequada para chat interativo.
    gemini_model: str = "gemini-2.5-flash"


settings = NLUSettings()
