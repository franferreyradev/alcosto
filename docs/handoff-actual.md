## HANDOFF — 2026-05-01 — T4 Conexión a PostgreSQL y repositorios base

### Tarea completada
- ID y nombre: T4 — Conexión a PostgreSQL y repositorios base
- Archivos creados/modificados:
  - `apps/api/app/config.py` → agregado campo `DEBUG: bool = False`
  - `apps/api/app/database.py` → engine async, AsyncSessionLocal, get_db
  - `apps/api/app/models/base.py` → Base (DeclarativeBase 2.0), TimestampMixin, CreatedAtMixin
  - `apps/api/app/models/category.py` → ORM tabla categories (sin timestamps)
  - `apps/api/app/models/product.py` → ORM tabla products (code manual, soft delete)
  - `apps/api/app/models/customer.py` → ORM tabla customers (solo created_at)
  - `apps/api/app/models/order.py` → ORM tabla orders (OrderStatus enum, total_amount inmutable)
  - `apps/api/app/models/order_item.py` → ORM tabla order_items (unit_price inmutable por trigger)
  - `apps/api/app/models/admin_user.py` → ORM tabla admin_users (AdminRole enum, solo created_at)
  - `apps/api/app/models/__init__.py` → barrel de todos los modelos
  - `apps/api/app/repositories/product_repo.py` → ProductRepo CRUD sin lógica de negocio
  - `apps/api/app/repositories/order_repo.py` → OrderRepo con selectinload y create atómico
  - `apps/api/app/repositories/__init__.py` → barrel de repositorios
  - `apps/api/tests/test_t4_integration.py` → 6 tests de integración con testcontainers
- Criterio de done verificado: sí ✓
- Comando de verificación ejecutado y resultado:
  ```
  pytest tests/test_t4_integration.py -v → 6/6 PASSED
  npx tsc --noEmit --project apps/web/tsconfig.json → sin errores
  ```

### Decisiones locales tomadas
- **asyncpg vs psycopg2 — DBAPIError**: asyncpg mapea `RAISE EXCEPTION` de PostgreSQL como `sqlalchemy.exc.DBAPIError`, no como `InternalError` (que es el mapping de psycopg2). El test `test_rn07_trigger_activo_via_orm` usa `DBAPIError` por esta razón.
- **ENUMs PostgreSQL**: `native_enum=True` + `create_type=False` en todos los SAEnum. `create_type=False` evita que SQLAlchemy intente crear el TYPE (ya existe por Alembic T2).
- **TimestampMixin vs CreatedAtMixin**: El schema de T2 tiene timestamps asimétricos. `products` y `orders` tienen ambos. `customers` y `admin_users` solo `created_at`. `categories` y `order_items` sin timestamps. Se crearon dos mixins.
- **docker teardown error**: testcontainers intenta forzar-remover el container al terminar pero el daemon retorna 500. Es cosmético — no afecta tests. Mismo gotcha de T2.

### Problemas conocidos
- El `ERROR` al teardown de testcontainers ("permission denied") aparece en cada corrida pero no bloquea ningún test ni CI.

### Tarea siguiente
- ID y nombre: T5 — Módulo Auth: login con JWT
- Depende de: T4 ✓
- Primer paso concreto: crear `apps/api/app/core/security.py` con `hash_password()`, `verify_password()` (passlib bcrypt cost=12), `create_access_token()` y `create_refresh_token()` (python-jose).
- Archivos a leer primero:
  - `docs/PLAN.md` Sección 3 (endpoints `/admin/auth/login` y `/admin/auth/refresh`) y Sección 4 T5 (criterio de done con los 3 casos de test)
  - `docs/PLAN.md` Sección 4 T6 (leerlo junto con T5 antes de arrancar)
  - `apps/api/app/models/admin_user.py` → el modelo ya tiene `password_hash` y `role`
- Nota: T5 y T6 van juntos conceptualmente — conviene leer el criterio de done de ambas antes de arrancar T5.
