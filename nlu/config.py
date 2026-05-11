"""Configurações da camada NLU (chat com Google Gemini).

Lidas via Pydantic Settings a partir do .env ou do ambiente do processo.
Os defaults só servem para desenvolvimento local — em execução real, a
chave de API tem de vir do ambiente.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class NLUSettings(BaseSettings):
    """Conjunto de configurações da camada NLU."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Chave de API do Google Gemini. Obrigatória em execução real.
    gemini_api_key: str = ""

    # Identificador do modelo Gemini usado pelo cliente. Flash 2.0 cobre
    # function calling e tem latência adequada para chat interativo.
    gemini_model: str = "gemini-2.0-flash"


settings = NLUSettings()
