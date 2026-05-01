## HANDOFF — 2026-04-30 — T2 Schema SQL inicial y migraciones Alembic

### Tarea completada
- ID y nombre: T2 — Schema SQL inicial y migraciones Alembic
- Archivos creados/modificados:
  - `apps/api/pyproject.toml` → agregado `psycopg2-binary` en deps de producción (Alembic lo necesita en Railway)
  - `apps/api/alembic.ini` → config Alembic, sqlalchemy.url vacío (se inyecta desde env.py), file_template con rev+slug
  - `apps/api/alembic/env.py` → importa settings desde app.config, reemplaza `postgresql+asyncpg://` → `postgresql://` para driver sync
  - `apps/api/alembic/script.py.mako` → template estándar para generación de futuras migraciones
  - `apps/api/alembic/versions/001_initial_schema.py` → rev `a1b2c3d4e5f6` — 6 tablas, 2 ENUMs, 12 índices (GIN full-text, parciales)
  - `apps/api/alembic/versions/002_triggers_inmutabilidad.py` → rev `b2c3d4e5f6a1` — fn_block_unit_price_update + fn_block_total_amount_update (RN-07)
  - `apps/api/alembic/versions/003_seed_admin_user.py` → rev `c3d4e5f6a1b2` — seed admin@alcosto.com, bcrypt cost 12, contraseña solo en stdout
  - `apps/api/tests/test_t2_schema.py` → 6 tests de integración con testcontainers + PostgreSQL real
- Criterio de done verificado: **sí — 6/6 tests verdes**
- Comando de verificación ejecutado y resultado:
  ```
  sudo env PATH="$PATH" .venv/bin/pytest tests/test_t2_schema.py -v
  6 passed in 3.20s
  ```

### Decisiones locales tomadas
- **Driver sync en Alembic**: `env.py` reemplaza `postgresql+asyncpg://` → `postgresql://` para que Alembic use psycopg2 (sync). SQLAlchemy async (T4) seguirá usando asyncpg con URL separada. Son dos engines distintos con propósitos distintos.
- **Contraseña admin**: generada con `secrets.token_urlsafe(12)`, hasheada con bcrypt rounds=12, impresa en stdout de la migración. No existe en ningún archivo ni en la DB en texto plano. No se puede recuperar después.
- **Mensajes de trigger exactos**: los strings `'order_items.unit_price es inmutable (RN-07)'` y `'orders.total_amount es inmutable (RN-07)'` son contratos de test — no modificar nunca.
- **`alembic_version` en information_schema**: Alembic crea esta tabla interna automáticamente. El test `test_seis_tablas_existen` la excluye explícitamente con `tables - {"alembic_version"}` para verificar solo las 6 tablas del dominio.
- **`sudo env PATH="$PATH"`**: necesario para que pytest dentro del venv tenga acceso al socket de Docker (testcontainers lo requiere).

### Problemas conocidos
- Ninguno. PR #2 mergeado.

### Tarea siguiente
- ID y nombre: T3 — Tipos compartidos en packages/shared
- Depende de: T1 ✓ (T2 NO es prerequisito de T3 — pueden correr en paralelo)
- Primer paso concreto: crear `packages/shared/src/entities/product.ts` con el tipo `Product` que refleja exactamente las columnas de la tabla `products` (code: number, name, price, stock, slug, is_active, category_id, image_url, description, created_at, updated_at)
- Archivos a leer primero:
  - `docs/PLAN.md` Sección 2 (esquema de DB para alinear tipos con columnas reales)
  - `docs/PLAN.md` Sección 4 T3 (criterio de done)
  - `packages/shared/src/index.ts` (barrel actual vacío)
