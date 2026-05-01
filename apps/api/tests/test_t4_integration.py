"""
Tests de integración T4 — SQLAlchemy 2.0 async, modelos ORM y repositorios base.

Levanta PostgreSQL real vía testcontainers, aplica las migraciones de T2
y verifica: engine async, CRUD vía repositorios, autoincrement=False (RN-01),
trigger RN-07 detectable vía ORM.
"""
import asyncio
import inspect
import os
import subprocess
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import text, update
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

POSTGRES_IMAGE = "postgres:16"
API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def db_url():
    with PostgresContainer(POSTGRES_IMAGE) as postgres:
        host = postgres.get_container_host_ip()
        port = postgres.get_exposed_port(5432)
        db = postgres.dbname
        user = postgres.username
        password = postgres.password

        async_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"
        env = {**os.environ, "DATABASE_URL": async_url}

        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=API_DIR,
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"alembic upgrade head falló:\n{result.stdout}\n{result.stderr}"
        )

        yield async_url


@pytest_asyncio.fixture
async def db_session(db_url):
    engine = create_async_engine(db_url, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
    await engine.dispose()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_engine_conecta(db_url):
    engine = create_async_engine(db_url, echo=False)
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
    await engine.dispose()


async def test_insert_y_read_producto(db_session):
    from app.models.category import Category
    from app.repositories.product_repo import ProductRepo

    cat = Category(name="Electrónica", slug="electronica-t4")
    db_session.add(cat)
    await db_session.flush()

    repo = ProductRepo()
    product = await repo.create(
        db_session,
        {
            "code": 1001,
            "name": "Televisor 55'",
            "description": "Full HD 55 pulgadas",
            "price": Decimal("150000.00"),
            "stock": 10,
            "category_id": cat.id,
            "slug": "televisor-55-t4",
            "is_active": True,
        },
    )

    # Leer de vuelta vía repositorio
    found = await repo.get_by_code(db_session, 1001)

    assert found is not None
    assert found.code == 1001, f"code fue alterado por la DB: {found.code} (RC-1)"
    assert found.name == "Televisor 55'"
    assert found.price == Decimal("150000.00")
    assert found.stock == 10
    assert found.is_active is True
    assert found.category_id == cat.id


async def test_code_exists(db_session):
    from app.models.category import Category
    from app.repositories.product_repo import ProductRepo

    cat = Category(name="Hogar", slug="hogar-t4")
    db_session.add(cat)
    await db_session.flush()

    repo = ProductRepo()
    await repo.create(
        db_session,
        {
            "code": 2002,
            "name": "Silla",
            "price": Decimal("5000.00"),
            "stock": 50,
            "category_id": cat.id,
            "slug": "silla-t4",
        },
    )

    assert await repo.code_exists(db_session, 2002) is True
    assert await repo.code_exists(db_session, 99999) is False


async def test_get_db_es_async_generator(db_url):
    from app import database as db_module

    assert inspect.isasyncgenfunction(db_module.get_db)

    engine = create_async_engine(db_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    original = db_module.AsyncSessionLocal
    db_module.AsyncSessionLocal = factory
    try:
        gen = db_module.get_db()
        session = await gen.__anext__()
        assert isinstance(session, AsyncSession)
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass
    finally:
        db_module.AsyncSessionLocal = original
        await engine.dispose()


def test_modelos_importan_correctamente():
    from app.models import (
        AdminUser,
        Base,
        Category,
        Customer,
        Order,
        OrderItem,
        Product,
    )

    assert Category.__tablename__ == "categories"
    assert Product.__tablename__ == "products"
    assert Customer.__tablename__ == "customers"
    assert Order.__tablename__ == "orders"
    assert OrderItem.__tablename__ == "order_items"
    assert AdminUser.__tablename__ == "admin_users"


async def test_rn07_trigger_activo_via_orm(db_session):
    from app.models.category import Category
    from app.models.customer import Customer
    from app.models.order import Order, OrderStatus
    from app.models.order_item import OrderItem
    from app.models.product import Product

    # Seed: category + product
    cat = Category(name="Trigger Cat", slug="trigger-cat-t4")
    db_session.add(cat)
    await db_session.flush()

    prod = Product(
        code=3003,
        name="Prod RN07",
        price=Decimal("1000.00"),
        stock=100,
        category_id=cat.id,
        slug="prod-rn07-t4",
    )
    db_session.add(prod)
    await db_session.flush()

    # Seed: customer + order + item
    customer = Customer(name="Cliente RN07", email="rn07-t4@test.com")
    db_session.add(customer)
    await db_session.flush()

    order = Order(
        customer_id=customer.id,
        status=OrderStatus.pending,
        total_amount=Decimal("65000.00"),
    )
    db_session.add(order)
    await db_session.flush()

    item = OrderItem(
        order_id=order.id,
        product_code=prod.code,
        quantity=65,
        unit_price=Decimal("1000.00"),
        subtotal=Decimal("65000.00"),
    )
    db_session.add(item)
    await db_session.flush()

    # El trigger debe bloquear cualquier UPDATE a unit_price
    # asyncpg mapea RAISE EXCEPTION como DBAPIError (no InternalError como psycopg2)
    with pytest.raises(DBAPIError, match="unit_price es inmutable"):
        await db_session.execute(
            update(OrderItem)
            .where(OrderItem.id == item.id)
            .values(unit_price=Decimal("999.00"))
        )
