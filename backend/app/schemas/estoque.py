"""Schemas Pydantic de entrada e saída para o Estoque."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


StatusSemaforo = Literal["verde", "amarelo", "vermelho"]


class EstoqueCreate(BaseModel):
    """Dados para inicializar um registro de estoque (Produto x Usuário)."""

    produto_id: int = Field(gt=0)
    usuario_id: int = Field(gt=0)
    quantidade: int = Field(ge=0)
    ponto_reposicao: int = Field(ge=0)
    ponto_amarelo: int = Field(gt=0)

    @model_validator(mode="after")
    def _validar_faixas_semaforo(self) -> "EstoqueCreate":
        # RN-06: a faixa amarela tem de ser estritamente maior que a de reposição,
        # caso contrário o intervalo "Amarelo" some e o semáforo perde uma faixa.
        if self.ponto_amarelo <= self.ponto_reposicao:
            raise ValueError(
                "ponto_amarelo deve ser maior que ponto_reposicao (RN-06)."
            )
        return self


class EstoqueRead(BaseModel):
    """Resposta pública de um registro de estoque.

    Não inclui o status Verde/Amarelo/Vermelho — derivação fica na service,
    porque é regra de apresentação (RN-06), não fato persistido.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    produto_id: int
    usuario_id: int
    quantidade: int
    ponto_reposicao: int
    ponto_amarelo: int


class EstoqueComStatusRead(EstoqueRead):
    """Estoque com o status do semáforo Kanban derivado (RN-06).

    O service `estoque.py` calcula o status e devolve dict com este shape;
    o schema apenas valida e serializa.
    """

    status: StatusSemaforo


class EstoqueUrgenteRead(EstoqueComStatusRead):
    """Estoque crítico priorizado pelo heap de reposição.

    Inclui `deficit` (= quantidade - ponto_reposicao): valor negativo indica
    consumo abaixo do ponto de reposição (vermelho), positivo entre as duas
    faixas (amarelo). Verdes não aparecem na lista.
    """

    deficit: int


class ConfigurarPontosInput(BaseModel):
    """Input PATCH /usuario/estoque/{produto_id}/pontos."""

    ponto_reposicao: int = Field(ge=0)
    ponto_amarelo: int = Field(gt=0)

    @model_validator(mode="after")
    def _validar_faixas_semaforo(self) -> "ConfigurarPontosInput":
        if self.ponto_amarelo <= self.ponto_reposicao:
            raise ValueError(
                "ponto_amarelo deve ser maior que ponto_reposicao (RN-06)."
            )
        return self
