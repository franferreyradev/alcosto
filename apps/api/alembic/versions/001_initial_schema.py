"""initial schema — 6 tablas, ENUMs, índices

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-04-30
"""
from typing import Sequence, Union
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ENUMs primero (no tienen dependencias)
    op.execute("CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'dispatched', 'cancelled')")
    op.execute("CREATE TYPE admin_role AS ENUM ('admin', 'staff')")

    # categories (sin FKs)
    op.execute("""
        CREATE TABLE categories (
            id   SERIAL       PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(100) NOT NULL UNIQUE
        )
    """)
    op.execute("CREATE INDEX idx_categories_slug ON categories(slug)")

    # admin_users (sin FKs)
    op.execute("""
        CREATE TABLE admin_users (
            id            SERIAL       PRIMARY KEY,
            email         VARCHAR(255) NOT NULL UNIQUE,
            password_hash TEXT         NOT NULL,
            role          admin_role   NOT NULL DEFAULT 'staff',
            is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_admin_users_email ON admin_users(email) WHERE is_active = TRUE")

    # customers (sin FKs)
    op.execute("""
        CREATE TABLE customers (
            id         SERIAL       PRIMARY KEY,
            name       VARCHAR(255) NOT NULL,
            email      VARCHAR(255) NOT NULL UNIQUE,
            phone      VARCHAR(50),
            address    TEXT,
            created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_customers_email ON customers(email)")

    # products (FK → categories)
    # code es INTEGER PRIMARY KEY manual — implementa RN-01 (no SERIAL)
    op.execute("""
        CREATE TABLE products (
            code        INTEGER        PRIMARY KEY,
            name        VARCHAR(255)   NOT NULL,
            description TEXT,
            price       NUMERIC(12,2)  NOT NULL CHECK (price >= 0),
            stock       INTEGER        NOT NULL DEFAULT 0 CHECK (stock >= 0),
            category_id INTEGER        REFERENCES categories(id) ON DELETE SET NULL,
            image_url   TEXT,
            slug        VARCHAR(255)   NOT NULL UNIQUE,
            is_active   BOOLEAN        NOT NULL DEFAULT TRUE,
            created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_products_active ON products(is_active) WHERE is_active = TRUE")
    op.execute("CREATE INDEX idx_products_category ON products(category_id)")
    op.execute("CREATE INDEX idx_products_slug ON products(slug)")
    op.execute("CREATE INDEX idx_products_name_search ON products USING gin(to_tsvector('spanish', name))")

    # orders (FK → customers)
    # CHECK total_amount >= 60000 implementa RN-05 como última defensa en DB
    op.execute("""
        CREATE TABLE orders (
            id           SERIAL        PRIMARY KEY,
            customer_id  INTEGER       NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
            status       order_status  NOT NULL DEFAULT 'pending',
            total_amount NUMERIC(12,2) NOT NULL CHECK (total_amount >= 60000),
            notes        TEXT,
            created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX idx_orders_status ON orders(status)")
    op.execute("CREATE INDEX idx_orders_created ON orders(created_at DESC)")
    op.execute("CREATE INDEX idx_orders_customer ON orders(customer_id)")

    # order_items (FK → orders CASCADE, FK → products RESTRICT)
    # ON DELETE RESTRICT en product_code implementa RN-02 a nivel físico
    op.execute("""
        CREATE TABLE order_items (
            id           SERIAL        PRIMARY KEY,
            order_id     INTEGER       NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
            product_code INTEGER       NOT NULL REFERENCES products(code) ON DELETE RESTRICT,
            quantity     INTEGER       NOT NULL CHECK (quantity > 0),
            unit_price   NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
            subtotal     NUMERIC(12,2) NOT NULL CHECK (subtotal >= 0)
        )
    """)
    op.execute("CREATE INDEX idx_order_items_order ON order_items(order_id)")
    op.execute("CREATE INDEX idx_order_items_product ON order_items(product_code)")


def downgrade() -> None:
    # Orden inverso al de upgrade (respeta dependencias de FK)
    op.execute("DROP TABLE IF EXISTS order_items")
    op.execute("DROP TABLE IF EXISTS orders")
    op.execute("DROP TABLE IF EXISTS products")
    op.execute("DROP TABLE IF EXISTS customers")
    op.execute("DROP TABLE IF EXISTS admin_users")
    op.execute("DROP TABLE IF EXISTS categories")
    op.execute("DROP TYPE IF EXISTS admin_role")
    op.execute("DROP TYPE IF EXISTS order_status")
