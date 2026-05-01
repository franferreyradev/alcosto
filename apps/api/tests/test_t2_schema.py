"""
Tests de integración T2 — Schema SQL inicial y migraciones Alembic.

Levanta un PostgreSQL real vía testcontainers, aplica las 3 migraciones
y verifica: tablas, INSERT en cascada, triggers RN-07, CHECK RN-05, RESTRICT RN-02.
"""
import os
import subprocess
import pytest
import psycopg2
import psycopg2.errors
from testcontainers.postgres import PostgresContainer

POSTGRES_IMAGE = "postgres:16"
API_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="session")
def db_conn():
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

        sync_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
        conn = psycopg2.connect(sync_url)
        conn.autocommit = True
        yield conn
        conn.close()


@pytest.fixture(scope="session")
def base_data(db_conn):
    cur = db_conn.cursor()

    cur.execute(
        "INSERT INTO categories (name, slug) VALUES ('Categoría Test', 'categoria-test') RETURNING id"
    )
    cat_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO products (code, name, price, stock, category_id, slug) "
        "VALUES (1001, 'Producto Test', 1000.00, 100, %s, 'producto-test') RETURNING code",
        (cat_id,),
    )
    product_code = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO customers (name, email) VALUES ('Cliente Test', 'cliente@test.com') RETURNING id"
    )
    customer_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO orders (customer_id, status, total_amount) "
        "VALUES (%s, 'pending', 65000.00) RETURNING id",
        (customer_id,),
    )
    order_id = cur.fetchone()[0]

    cur.execute(
        "INSERT INTO order_items (order_id, product_code, quantity, unit_price, subtotal) "
        "VALUES (%s, %s, 65, 1000.00, 65000.00) RETURNING id",
        (order_id, product_code),
    )
    item_id = cur.fetchone()[0]

    return {
        "cat_id": cat_id,
        "product_code": product_code,
        "customer_id": customer_id,
        "order_id": order_id,
        "item_id": item_id,
    }


def test_seis_tablas_existen(db_conn):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' ORDER BY table_name"
    )
    tables = {row[0] for row in cur.fetchall()}
    expected = {"categories", "products", "customers", "orders", "order_items", "admin_users"}
    assert expected == tables - {"alembic_version"}, f"Tablas encontradas: {tables}"


def test_insert_order_items_valido(db_conn, base_data):
    cur = db_conn.cursor()
    cur.execute(
        "SELECT unit_price, subtotal FROM order_items WHERE id = %s",
        (base_data["item_id"],),
    )
    row = cur.fetchone()
    assert row is not None, "order_item no existe después del INSERT"
    assert float(row[0]) == 1000.00
    assert float(row[1]) == 65000.00


def test_rn07_unit_price_inmutable(db_conn, base_data):
    cur = db_conn.cursor()
    try:
        cur.execute(
            "UPDATE order_items SET unit_price = 999 WHERE id = %s",
            (base_data["item_id"],),
        )
        pytest.fail("El trigger debería haber bloqueado el UPDATE de unit_price")
    except psycopg2.errors.RaiseException as e:
        assert "order_items.unit_price es inmutable (RN-07)" in str(e)


def test_rn07_price_change_no_afecta_historial(db_conn, base_data):
    cur = db_conn.cursor()
    cur.execute(
        "UPDATE products SET price = 9999.99 WHERE code = %s",
        (base_data["product_code"],),
    )
    cur.execute(
        "SELECT unit_price FROM order_items WHERE id = %s",
        (base_data["item_id"],),
    )
    unit_price = float(cur.fetchone()[0])
    assert unit_price == 1000.00, (
        f"unit_price cambió a {unit_price} después de actualizar products.price — viola RN-07"
    )


def test_total_amount_check_constraint(db_conn, base_data):
    cur = db_conn.cursor()
    try:
        cur.execute(
            "INSERT INTO orders (customer_id, status, total_amount) "
            "VALUES (%s, 'pending', 50000.00)",
            (base_data["customer_id"],),
        )
        pytest.fail("El CHECK constraint debería haber rechazado total_amount < 60000")
    except psycopg2.errors.CheckViolation:
        pass


def test_soft_delete_restrict(db_conn, base_data):
    cur = db_conn.cursor()
    try:
        cur.execute(
            "DELETE FROM products WHERE code = %s",
            (base_data["product_code"],),
        )
        pytest.fail("La FK ON DELETE RESTRICT debería haber bloqueado el DELETE de products")
    except psycopg2.errors.ForeignKeyViolation:
        pass
