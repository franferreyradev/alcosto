"""triggers de inmutabilidad RN-07

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-04-30
"""
from typing import Sequence, Union
from alembic import op

revision: str = "b2c3d4e5f6a1"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Trigger 1: bloquea UPDATE sobre order_items.unit_price (RN-07)
    # Mensaje exacto verificado por tests — no modificar el texto
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_block_unit_price_update()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.unit_price IS DISTINCT FROM OLD.unit_price THEN
                RAISE EXCEPTION 'order_items.unit_price es inmutable (RN-07)';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_block_unit_price_update
        BEFORE UPDATE ON order_items
        FOR EACH ROW EXECUTE FUNCTION fn_block_unit_price_update()
    """)

    # Trigger 2: bloquea UPDATE sobre orders.total_amount (RN-07)
    # Mensaje exacto verificado por tests — no modificar el texto
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_block_total_amount_update()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.total_amount IS DISTINCT FROM OLD.total_amount THEN
                RAISE EXCEPTION 'orders.total_amount es inmutable (RN-07)';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_block_total_amount_update
        BEFORE UPDATE ON orders
        FOR EACH ROW EXECUTE FUNCTION fn_block_total_amount_update()
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_block_total_amount_update ON orders")
    op.execute("DROP FUNCTION IF EXISTS fn_block_total_amount_update()")
    op.execute("DROP TRIGGER IF EXISTS trg_block_unit_price_update ON order_items")
    op.execute("DROP FUNCTION IF EXISTS fn_block_unit_price_update()")
