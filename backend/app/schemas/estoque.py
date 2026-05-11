"""Schemas Pydantic de entrada e saída para o Estoque."""
from pydantic import BaseModel, ConfigDict, Field, model_validator


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
