from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order
from app.models.order_item import OrderItem


class OrderRepo:
    async def get_by_id(self, session: AsyncSession, order_id: int) -> Order | None:
        result = await session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items), selectinload(Order.customer))
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Order]:
        stmt = select(Order)
        if status is not None:
            stmt = stmt.where(Order.status == status)
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(
        self, session: AsyncSession, order_data: dict, items_data: list[dict]
    ) -> Order:
        order = Order(**order_data)
        session.add(order)
        await session.flush()

        for item_data in items_data:
            item = OrderItem(order_id=order.id, **item_data)
            session.add(item)

        await session.flush()
        return order
