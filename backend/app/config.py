"""Configurações da aplicação carregadas a partir de variáveis de ambiente.

Usamos Pydantic Settings para validar e tipar as variáveis. Os defaults
servem apenas para o ambiente de desenvolvimento local — em produção é
obrigatório fornecer um arquivo .env com os valores reais.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Conjunto de configurações lidas de .env ou do ambiente do processo."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # URL de conexão com o banco. SQLite local em dev; PostgreSQL em prod.
    database_url: str = "sqlite:///./vmi.db"

    # Chave secreta usada para assinar JWTs. Em produção, sempre via .env.
    secret_key: str = "dev-only-change-me-in-production"

    # Algoritmo de assinatura do JWT.
    jwt_algorithm: str = "HS256"

    # Tempo de validade do access token em minutos.
    jwt_expire_minutes: int = 60


# Instância única usada em toda a aplicação.
settings = Settings()
