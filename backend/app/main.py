"""Ponto de entrada da API VMI Chat.

Cria a aplicação FastAPI e registra os routers. As rotas em si vivem em
`app/routes/` — este arquivo só compõe a aplicação.
"""
from fastapi import FastAPI

from app.routes import health

app = FastAPI(
    title="VMI Chat API",
    version="0.1.0",
    description="API do sistema de Vendor Managed Inventory.",
)

# Registramos cada router separadamente para manter a composição explícita.
app.include_router(health.router)
