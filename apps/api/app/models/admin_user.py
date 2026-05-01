from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum as SAEnum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin


class AdminRole(str, enum.Enum):
    admin = "admin"
    staff = "staff"


class AdminUser(CreatedAtMixin, Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # password_hash nunca se incluye en schemas Pydantic de response (se controla en T5)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[AdminRole] = mapped_column(
        SAEnum(AdminRole, name="admin_role", native_enum=True, create_type=False),
        nullable=False,
        server_default="staff",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
