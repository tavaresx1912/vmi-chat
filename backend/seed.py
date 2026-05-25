"""Wipe and reseed the local SQLite DB with one user per role + sample data.

Run from the backend/ directory:
    .venv/Scripts/python.exe seed.py
"""
from decimal import Decimal

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models.estoque import Estoque
from app.models.fornecedor import Fornecedor
from app.models.pedido import ItemPedido, OrigemPedido, PedidoCompra, StatusPedido
from app.models.produto import Produto
from app.models.produto_fornecedor import ProdutoFornecedor
from app.models.user import User, UserRole


def main() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Delete order respects FK constraints: leaves at children.
        db.query(ItemPedido).delete()
        db.query(PedidoCompra).delete()
        db.query(Estoque).delete()
        db.query(ProdutoFornecedor).delete()
        db.query(Fornecedor).delete()
        db.query(Produto).delete()
        db.query(User).delete()
        db.commit()

        admin = User(
            nome="Ana Admin",
            email="admin@vmi.test.br",
            senha_hash=hash_password("admin123"),
            role=UserRole.ADMIN,
            ativo=True,
        )
        cliente = User(
            nome="Carlos Cliente",
            email="cliente@vmi.test.br",
            senha_hash=hash_password("cliente123"),
            role=UserRole.USUARIO,
            ativo=True,
        )
        fornecedor_user = User(
            nome="Fabio Fornecedor",
            email="fornecedor@vmi.test.br",
            senha_hash=hash_password("fornecedor123"),
            role=UserRole.FORNECEDOR,
            ativo=True,
        )
        db.add_all([admin, cliente, fornecedor_user])
        db.flush()

        fornecedor = Fornecedor(
            user_id=fornecedor_user.id,
            nome="Distribuidora Exemplo Ltda",
            cnpj="12345678000190",
        )
        db.add(fornecedor)
        db.flush()

        parafuso = Produto(
            nome="Parafuso M6 20mm",
            descricao="Parafuso sextavado aço inox",
            categoria="Ferragens",
        )
        luva = Produto(
            nome="Luva Nitrílica G",
            descricao="Luva de proteção descartável tamanho G",
            categoria="EPI",
        )
        resma = Produto(
            nome="Resma A4 75g",
            descricao="Pacote com 500 folhas",
            categoria="Escritório",
        )
        db.add_all([parafuso, luva, resma])
        db.flush()

        pf_parafuso = ProdutoFornecedor(
            produto_id=parafuso.id,
            fornecedor_id=fornecedor.id,
            preferencial=True,
            preco_contratado=Decimal("0.45"),
            prazo_entrega_dias=3,
            qtd_minima_pedido=100,
        )
        pf_luva = ProdutoFornecedor(
            produto_id=luva.id,
            fornecedor_id=fornecedor.id,
            preferencial=True,
            preco_contratado=Decimal("28.90"),
            prazo_entrega_dias=5,
            qtd_minima_pedido=10,
        )
        pf_resma = ProdutoFornecedor(
            produto_id=resma.id,
            fornecedor_id=fornecedor.id,
            preferencial=True,
            preco_contratado=Decimal("24.00"),
            prazo_entrega_dias=2,
            qtd_minima_pedido=5,
        )
        db.add_all([pf_parafuso, pf_luva, pf_resma])
        db.flush()

        db.add_all(
            [
                Estoque(
                    produto_id=parafuso.id,
                    usuario_id=cliente.id,
                    quantidade=80,
                    ponto_reposicao=50,
                    ponto_amarelo=120,
                ),
                Estoque(
                    produto_id=luva.id,
                    usuario_id=cliente.id,
                    quantidade=15,
                    ponto_reposicao=20,
                    ponto_amarelo=40,
                ),
                Estoque(
                    produto_id=resma.id,
                    usuario_id=cliente.id,
                    quantidade=8,
                    ponto_reposicao=5,
                    ponto_amarelo=15,
                ),
            ]
        )

        pedido = PedidoCompra(
            usuario_id=cliente.id,
            status=StatusPedido.PENDENTE,
            origem=OrigemPedido.MANUAL,
        )
        db.add(pedido)
        db.flush()

        db.add_all(
            [
                ItemPedido(
                    pedido_id=pedido.id,
                    produto_fornecedor_id=pf_parafuso.id,
                    quantidade=200,
                    preco_unitario=Decimal("0.45"),
                ),
                ItemPedido(
                    pedido_id=pedido.id,
                    produto_fornecedor_id=pf_luva.id,
                    quantidade=30,
                    preco_unitario=Decimal("28.90"),
                ),
            ]
        )

        db.commit()

        print("Seed OK")
        print(f"  admin      -> {admin.email} / admin123")
        print(f"  usuario    -> {cliente.email} / cliente123")
        print(f"  fornecedor -> {fornecedor_user.email} / fornecedor123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
