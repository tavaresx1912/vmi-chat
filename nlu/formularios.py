"""Spec dos formularios em chat para tools de escrita (PRD §11.4 + UX).

Descreve, por tool, a lista de Campos que o frontend renderiza no
cartao-de-acao. O modulo e agnostico de Streamlit: cada Campo carrega
apenas dados (nome, label, widget, fonte de dropdown como chave string).
O frontend (`frontend/cartao_confirmacao.py`) traduz `widget` em
componente concreto e `fonte_dropdown` em chamada HTTP via
`frontend/fontes_opcoes.py`.

Validacao continua nas classes Pydantic *Args dos arquivos
`tools_*.py` — esta spec descreve UI, nao regra de negocio.
"""
from dataclasses import dataclass, field
from typing import Literal

WidgetTipo = Literal[
    "text",       # st.text_input
    "password",   # st.text_input com type='password'
    "number",     # st.number_input inteiro
    "decimal",    # st.number_input com format de Decimal
    "select",     # st.selectbox com `opcoes` fixas
    "dropdown",   # st.selectbox alimentado por `fonte_dropdown` (HTTP)
    "itens",      # lista dinamica de sub-formularios (`itens_campos`)
]


@dataclass(frozen=True)
class Campo:
    """Descritor de um campo de formulario."""

    nome: str
    label: str
    widget: WidgetTipo
    # Para widget="select": tupla de opcoes fixas (ex.: papeis).
    opcoes: tuple[str, ...] = ()
    # Para widget="dropdown": chave em fontes_opcoes (ex.: "usuarios").
    fonte_dropdown: str = ""
    # Para widget="number"/"decimal": limite minimo da UI (validacao final
    # continua no Pydantic; o min aqui so evita digitar valor invalido).
    min_value: int | None = None
    # Texto de ajuda mostrado no widget (st.text_input help / placeholder).
    help: str = ""
    # Para widget="itens": campos de cada linha da lista dinamica.
    itens_campos: tuple["Campo", ...] = field(default_factory=tuple)


# Spec dos 6 forms cobrindo todas as escritas de admin + usuario (PRD §11.3).
CAMPOS_POR_TOOL: dict[str, tuple[Campo, ...]] = {
    "criar_usuario": (
        Campo("nome", "Nome", "text"),
        Campo("email", "Email", "text"),
        Campo("senha", "Senha", "password", help="Mínimo 6 caracteres."),
        Campo(
            "role",
            "Papel",
            "select",
            opcoes=("admin", "usuario", "fornecedor"),
        ),
    ),
    "desativar_usuario": (
        Campo("usuario_id", "Usuário", "dropdown", fonte_dropdown="usuarios"),
    ),
    "cadastrar_produto": (
        Campo("nome", "Nome do produto", "text"),
        Campo("categoria", "Categoria", "text"),
        Campo(
            "fornecedor_id",
            "Fornecedor",
            "dropdown",
            fonte_dropdown="fornecedores",
        ),
        Campo(
            "preco_contratado",
            "Preço contratado (R$)",
            "decimal",
            min_value=0,
        ),
        Campo(
            "qtd_minima_pedido",
            "Quantidade mínima por pedido",
            "number",
            min_value=1,
        ),
    ),
    "configurar_pontos_reposicao": (
        # Catalogo completo: pode-se configurar pontos de um produto que
        # ainda nao tem registro de estoque (qtd=0 e criada no service).
        Campo(
            "produto_id",
            "Produto",
            "dropdown",
            fonte_dropdown="produtos_catalogo",
        ),
        Campo(
            "ponto_reposicao",
            "Ponto de reposição (limite Vermelho)",
            "number",
            min_value=0,
        ),
        Campo(
            "ponto_amarelo",
            "Ponto Amarelo (deve ser maior que reposição)",
            "number",
            min_value=1,
        ),
    ),
    "pedido_reposicao": (
        # So estoques ja configurados: RN-07 exige amarelo/vermelho.
        # Label exibe o status para o usuario escolher conscientemente.
        Campo(
            "produto_id",
            "Produto a repor",
            "dropdown",
            fonte_dropdown="produtos_estoque",
        ),
    ),
    "criar_pedido_manual": (
        Campo(
            "itens",
            "Itens do pedido",
            "itens",
            itens_campos=(
                Campo(
                    "produto_fornecedor_id",
                    "Item (produto + fornecedor)",
                    "dropdown",
                    fonte_dropdown="produtos_fornecedores",
                ),
                Campo("quantidade", "Quantidade", "number", min_value=1),
            ),
        ),
    ),
}


TOOLS_COM_FORM: frozenset[str] = frozenset(CAMPOS_POR_TOOL.keys())


def campos_de(tool: str) -> tuple[Campo, ...]:
    """Retorna os campos do formulario da tool, ou tupla vazia se desconhecida."""
    return CAMPOS_POR_TOOL.get(tool, ())
