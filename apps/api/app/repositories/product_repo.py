from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


class ProductRepo:
    async def get_by_code(self, session: AsyncSession, code: int) -> Product | None:
        result = await session.execute(select(Product).where(Product.code == code))
        return result.scalar_one_or_none()

    async def get_by_slug(self, session: AsyncSession, slug: str) -> Product | None:
        result = await session.execute(select(Product).where(Product.slug == slug))
        return result.scalar_one_or_none()

    async def get_all(
        self,
        session: AsyncSession,
        include_inactive: bool = False,
        category_id: int | None = None,
        search: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Product]:
        stmt = select(Product)
        if not include_inactive:
            stmt = stmt.where(Product.is_active.is_(True))
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)
        if search is not None:
            stmt = stmt.where(Product.name.ilike(f"%{search}%"))
        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, data: dict) -> Product:
        product = Product(**data)
        session.add(product)
        await session.flush()
        return product

    async def update(self, session: AsyncSession, code: int, data: dict) -> Product | None:
        product = await self.get_by_code(session, code)
        if product is None:
            return None
        for key, value in data.items():
            setattr(product, key, value)
        await session.flush()
        return product

    async def code_exists(self, session: AsyncSession, code: int) -> bool:
        result = await session.execute(
            select(exists().where(Product.code == code))
        )
        return bool(result.scalar())
