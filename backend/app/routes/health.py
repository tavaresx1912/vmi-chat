"""Endpoint de healthcheck.

Serve para verificar rapidamente se a API subiu corretamente. Útil para
monitoramento, smoke tests e validação pós-deploy.
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Resposta padrão do healthcheck."""

    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    """Retorna o status atual da API e a versão da aplicação."""
    return HealthResponse(status="ok", version="0.1.0")
