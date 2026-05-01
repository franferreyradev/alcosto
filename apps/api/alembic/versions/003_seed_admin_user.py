"""seed usuario admin inicial

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-04-30
"""
import secrets
from typing import Sequence, Union

from alembic import op
from passlib.hash import bcrypt
from sqlalchemy import text

revision: str = "c3d4e5f6a1b2"
down_revision: Union[str, None] = "b2c3d4e5f6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    password = secrets.token_urlsafe(12)
    password_hash = bcrypt.using(rounds=12).hash(password)

    print("=" * 60)
    print("CONTRASEÑA ADMIN TEMPORAL:", password)
    print("Cambiarla en el primer login. No se puede recuperar.")
    print("=" * 60)

    bind = op.get_bind()
    bind.execute(
        text(
            "INSERT INTO admin_users (email, password_hash, role, is_active) "
            "VALUES (:email, :phash, 'admin', TRUE)"
        ),
        {"email": "admin@alcosto.com", "phash": password_hash},
    )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        text("DELETE FROM admin_users WHERE email = :email"),
        {"email": "admin@alcosto.com"},
    )
