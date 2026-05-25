"""Despacho de tool calls para endpoints HTTP do backend.

Tabela `DESPACHO` mapeia o nome de cada tool (catalogo Ingrid, C4) para
o endpoint correspondente do backend (C2): metodo HTTP, template de
path, e estrategia de monte de payload/query.

Por que aqui (nlu) e nao em frontend: este e o ponto de contrato entre
tool name e endpoint REST — dono e Guilherme (C2). O frontend so consome
`executar_tool(tool, args)` sem precisar conhecer rotas.

A chamada HTTP propriamente dita e feita por uma funcao injetada
(`http_call`) para nao acoplar a camada NLU ao httpx do frontend.
"""
from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from .filtro_tools import schemas_args_para_papel


# Assinatura da funcao HTTP injetada pelo orquestrador (frontend).
# Recebe (metodo, path, json|None, params|None) e devolve o JSON da
# resposta. Excecoes da camada de transporte sobem para o caller.
HttpCall = Callable[[str, str, Any, dict[str, Any] | None], Any]


@dataclass(frozen=True)
class EndpointSpec:
    """Especificacao de como uma tool vira chamada HTTP."""

    metodo: str
    # Template do path com placeholders {nome_arg}. Ex.: /admin/usuarios/{usuario_id}/desativar
    path_template: str
    # Args que sao consumidos do path; ficam fora do body/query.
    args_no_path: tuple[str, ...] = ()
    # Args que vao para query string (GET). Os demais vao para o body (POST/PATCH).
    args_em_query: tuple[str, ...] = ()


DESPACHO: dict[str, EndpointSpec] = {
    # --- Admin ---
    "criar_usuario": EndpointSpec("POST", "/admin/usuarios"),
    "listar_usuarios": EndpointSpec(
        "GET", "/admin/usuarios", args_em_query=("filtro",)
    ),
    "desativar_usuario": EndpointSpec(
        "POST",
        "/admin/usuarios/{usuario_id}/desativar",
        args_no_path=("usuario_id",),
    ),
    # --- Usuario ---
    "buscar_produtos": EndpointSpec(
        "GET", "/usuario/produtos", args_em_query=("termo", "categoria")
    ),
    "cadastrar_produto": EndpointSpec("POST", "/usuario/produtos"),
    "consultar_estoque": EndpointSpec("GET", "/usuario/estoque"),
    "configurar_pontos_reposicao": EndpointSpec(
        "PATCH",
        "/usuario/estoque/{produto_id}/pontos",
        args_no_path=("produto_id",),
    ),
    "criar_pedido_manual": EndpointSpec("POST", "/usuario/pedidos"),
    "pedido_reposicao": EndpointSpec("POST", "/usuario/pedidos/reposicao"),
    "listar_pedidos": EndpointSpec(
        "GET", "/usuario/pedidos", args_em_query=("filtro",)
    ),
    # --- Fornecedor ---
    "atualizar_estoque": EndpointSpec("PATCH", "/fornecedor/estoque"),
    "atualizar_status_pedido": EndpointSpec(
        "PATCH",
        "/fornecedor/pedidos/{pedido_id}/status",
        args_no_path=("pedido_id",),
    ),
}


class ToolForaDoEscopoError(Exception):
    """Tool nao visivel para o papel atual (provavel hallucination)."""


class ArgsInvalidosError(Exception):
    """Args nao passam pelo schema Pydantic da tool."""

    def __init__(self, tool: str, erros: str) -> None:
        super().__init__(f"{tool}: {erros}")
        self.tool = tool
        self.erros = erros


def _validar_args(
    tool: str, args: dict[str, Any], role: str
) -> dict[str, Any]:
    """Valida com o Pydantic da tool (filtrado por papel) e devolve dict serializavel."""
    schemas = schemas_args_para_papel(role)
    schema = schemas.get(tool)
    if schema is None:
        raise ToolForaDoEscopoError(tool)
    try:
        modelo = schema(**args)
    except ValidationError as e:
        # Compacta a lista de erros do Pydantic em uma string curta pt-br.
        partes = [f"{'.'.join(map(str, err['loc']))}: {err['msg']}" for err in e.errors()]
        raise ArgsInvalidosError(tool, "; ".join(partes)) from e
    # mode="json" converte Decimal->str, Enum->valor, etc., pronto pra httpx.
    return modelo.model_dump(mode="json", exclude_none=True)


def _montar_chamada(
    spec: EndpointSpec, dados: dict[str, Any]
) -> tuple[str, str, Any, dict[str, Any] | None]:
    """Aplica a EndpointSpec ao dict ja validado e retorna (metodo, path, body, params)."""
    # 1. Extrai args do path e formata o template.
    valores_path: dict[str, Any] = {}
    restantes = dict(dados)
    for nome in spec.args_no_path:
        if nome in restantes:
            valores_path[nome] = restantes.pop(nome)
    path = spec.path_template.format(**valores_path)

    # 2. Separa query e body conforme a spec.
    params: dict[str, Any] | None = None
    body: Any = None
    if spec.args_em_query:
        params = {}
        for nome in spec.args_em_query:
            if nome in restantes:
                params[nome] = restantes.pop(nome)
        if not params:
            params = None

    # 3. O resto vai para o body — apenas em metodos com corpo.
    if spec.metodo in ("POST", "PATCH", "PUT") and restantes:
        body = restantes

    return spec.metodo, path, body, params


def executar_tool(
    *,
    tool: str,
    args: dict[str, Any],
    role: str,
    http_call: HttpCall,
) -> Any:
    """Valida args, despacha para o endpoint correspondente e devolve a resposta.

    `http_call` e injetado pelo orquestrador (frontend) para evitar
    acoplamento NLU<->httpx. Erros HTTP sobem como APIError do frontend
    diretamente — esta camada nao traduz.
    """
    spec = DESPACHO.get(tool)
    if spec is None:
        raise ToolForaDoEscopoError(tool)

    dados = _validar_args(tool, args, role)
    metodo, path, body, params = _montar_chamada(spec, dados)
    return http_call(metodo, path, body, params)
