from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.order_item import OrderItem


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    # RC-1: autoincrement=False — código manual asignado por el operador (RN-01)
    code: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # RN-02: soft delete — nunca hard delete de productos
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    category: Mapped[Category | None] = relationship("Category", back_populates="products")
    order_items: Mapped[list[OrderItem]] = relationship("OrderItem", back_populates="product")
