# PLAN.md — AlCosto: Plataforma Mayorista B2B

**Versión:** 2.0 — Refactorizado bajo plantilla SDD  
**Fecha:** Abril 2025  
**Documento padre:** SPEC.md v2.0  
**Rol de este documento:** Define el CÓMO. Materializa cada `RN-XX` del SPEC en decisiones técnicas verificables.

---

## SECCIÓN 1 — ARQUITECTURA DE CARPETAS

```
alcosto/
├── apps/
│   ├── web/                      → Next.js 14 (catálogo público + panel admin)
│   │   ├── app/                  → Rutas App Router con grupos (public)/(admin)
│   │   ├── components/           → Componentes atómicos y compuestos UI
│   │   ├── modules/              → Módulos de dominio (catalog, cart, admin-products, etc.)
│   │   ├── lib/                  → Cliente HTTP, hooks, utilidades frontend
│   │   ├── public/               → Assets estáticos (logo AlCosto, fuentes)
│   │   ├── styles/               → CSS global, configuración base de Tailwind
│   │   ├── middleware.ts         → Protección de rutas /admin/*
│   │   ├── next.config.js        → Configuración Next.js
│   │   ├── tailwind.config.ts    → Design tokens de marca
│   │   └── package.json          → Workspace del frontend
│   │
│   └── api/                      → FastAPI backend (API REST desacoplada)
│       ├── app/
│       │   ├── routers/          → Endpoints agrupados (public/, admin/)
│       │   ├── services/         → Lógica de negocio pura (testeable en aislamiento)
│       │   ├── repositories/     → Acceso a PostgreSQL (queries, transacciones)
│       │   ├── models/           → Modelos SQLAlchemy ORM
│       │   ├── schemas/          → DTOs Pydantic v2 (request/response)
│       │   ├── core/             → Auth, deps, security, exceptions
│       │   ├── config.py         → Settings vía pydantic-settings
│       │   ├── database.py       → Engine y session factory
│       │   └── main.py           → Entry point FastAPI + CORS + routers
│       ├── alembic/              → Migraciones SQL versionadas
│       │   └── versions/
│       ├── scripts/
│       │   └── migrate_from_wordpress.py  → Migración inicial (uso único)
│       ├── tests/                → pytest + testcontainers
│       ├── pyproject.toml
│       └── Dockerfile
│
├── packages/
│   └── shared/                   → Tipos TypeScript compartidos
│       ├── src/
│       │   ├── entities/         → Tipos del dominio (Product, Order, Customer, etc.)
│       │   ├── enums/            → ENUMs compartidos (OrderStatus, AdminRole)
│       │   └── contracts/        → DTOs de request/response de la API
│       └── package.json
│
├── docs/
│   ├── SPEC.md                   → Especificación funcional v2.0
│   ├── PLAN.md                   → Este documento
│   └── adr/                      → Architecture Decision Records (uno por decisión)
│
├── .github/
│   └── workflows/                → CI (lint, tests, deploy)
│
├── package.json                  → Raíz del monorepo con workspaces npm
├── tsconfig.base.json            → Configuración TypeScript compartida
├── .env.example                  → Plantilla de variables de entorno
└── README.md                     → Setup, scripts, convenciones
```

**Convenciones:**
- Cada módulo de `apps/web/modules/` es independiente; no importa código de otros módulos directamente. Se comunican vía `shared/` o vía API.
- En `apps/api/`, los routers solo orquestan. La lógica vive en `services/`. Los modelos ORM y los DTOs Pydantic nunca se mezclan.
- Server Components por defecto en Next.js. Client Components solo con `"use client"` explícito cuando hay interactividad.

---

## SECCIÓN 2 — ESQUEMA DE BASE DE DATOS

Cada tabla referencia las reglas de negocio del SPEC.md que justifican su diseño.

### Tipos personalizados (ENUMs PostgreSQL)

```sql
CREATE TYPE order_status AS ENUM ('pending', 'confirmed', 'dispatched', 'cancelled');
CREATE TYPE admin_role AS ENUM ('admin', 'staff');
```

### Tabla: categories

| Columna | Tipo         | Constraints                           |
|---------|--------------|---------------------------------------|
| id      | SERIAL       | PRIMARY KEY                           |
| name    | VARCHAR(100) | NOT NULL                              |
| slug    | VARCHAR(100) | NOT NULL UNIQUE                       |

**Índices:** `CREATE INDEX idx_categories_slug ON categories(slug);`

### Tabla: products

| Columna       | Tipo          | Constraints                                                |
|---------------|---------------|------------------------------------------------------------|
| code          | INTEGER       | PRIMARY KEY (asignado manualmente — `RN-01`)              |
| name          | VARCHAR(255)  | NOT NULL                                                   |
| description   | TEXT          | NULL (campo libre — `RN-03`)                              |
| price         | NUMERIC(12,2) | NOT NULL, CHECK (price >= 0)                               |
| stock         | INTEGER       | NOT NULL DEFAULT 0, CHECK (stock >= 0)                     |
| category_id   | INTEGER       | NULL, FK → categories(id) ON DELETE SET NULL              |
| image_url     | TEXT          | NULL                                                       |
| slug          | VARCHAR(255)  | NOT NULL UNIQUE                                            |
| is_active     | BOOLEAN       | NOT NULL DEFAULT TRUE                                      |
| created_at    | TIMESTAMPTZ   | NOT NULL DEFAULT NOW()                                     |
| updated_at    | TIMESTAMPTZ   | NOT NULL DEFAULT NOW()                                     |

**`code` como PK manual:** implementa `RN-01`. No es `SERIAL`. La aplicación valida unicidad antes de insertar y devuelve error específico si ya existe (endpoint `/admin/products/{code}/exists`).

**`is_active` para soft delete:** implementa `RN-02`. Nunca se borra físicamente. La FK desde `order_items.product_code` sin `CASCADE` impide el borrado físico aunque se intente.

**Índices:**
- `CREATE INDEX idx_products_active ON products(is_active) WHERE is_active = TRUE;`
- `CREATE INDEX idx_products_category ON products(category_id);`
- `CREATE INDEX idx_products_slug ON products(slug);`
- `CREATE INDEX idx_products_name_search ON products USING gin(to_tsvector('spanish', name));` (búsqueda full-text)

### Tabla: customers

| Columna     | Tipo         | Constraints                              |
|-------------|--------------|------------------------------------------|
| id          | SERIAL       | PRIMARY KEY                              |
| name        | VARCHAR(255) | NOT NULL                                 |
| email       | VARCHAR(255) | NOT NULL UNIQUE                          |
| phone       | VARCHAR(50)  | NULL                                     |
| address     | TEXT         | NULL                                     |
| created_at  | TIMESTAMPTZ  | NOT NULL DEFAULT NOW()                   |

**Índices:** `CREATE INDEX idx_customers_email ON customers(email);`

### Tabla: orders

| Columna       | Tipo          | Constraints                                                       |
|---------------|---------------|-------------------------------------------------------------------|
| id            | SERIAL        | PRIMARY KEY                                                       |
| customer_id   | INTEGER       | NOT NULL, FK → customers(id) ON DELETE RESTRICT                  |
| status        | order_status  | NOT NULL DEFAULT 'pending'                                        |
| total_amount  | NUMERIC(12,2) | NOT NULL, CHECK (total_amount >= 60000) — `RN-05`                |
| notes         | TEXT          | NULL                                                              |
| created_at    | TIMESTAMPTZ   | NOT NULL DEFAULT NOW()                                            |
| updated_at    | TIMESTAMPTZ   | NOT NULL DEFAULT NOW()                                            |

**`CHECK (total_amount >= 60000)`:** implementa `RN-05` a nivel de base de datos como última línea de defensa. Si el frontend o el servicio fallan en validar el mínimo, la DB rechaza el INSERT.

**Inmutabilidad de `total_amount` post-creación:** trigger `BEFORE UPDATE` que rechaza cambios a esta columna. Implementa `RN-07` extendido al monto total.

**Índices:**
- `CREATE INDEX idx_orders_status ON orders(status);`
- `CREATE INDEX idx_orders_created ON orders(created_at DESC);`
- `CREATE INDEX idx_orders_customer ON orders(customer_id);`

### Tabla: order_items

| Columna       | Tipo          | Constraints                                                       |
|---------------|---------------|-------------------------------------------------------------------|
| id            | SERIAL        | PRIMARY KEY                                                       |
| order_id      | INTEGER       | NOT NULL, FK → orders(id) ON DELETE CASCADE                      |
| product_code  | INTEGER       | NOT NULL, FK → products(code) ON DELETE RESTRICT                 |
| quantity      | INTEGER       | NOT NULL, CHECK (quantity > 0)                                    |
| unit_price    | NUMERIC(12,2) | NOT NULL, CHECK (unit_price >= 0)                                |
| subtotal      | NUMERIC(12,2) | NOT NULL, CHECK (subtotal >= 0)                                  |

**`product_code` con `ON DELETE RESTRICT`:** implementa `RN-02` a nivel físico. Imposible borrar un producto que tenga pedidos históricos. La única operación de retiro válida es `is_active = FALSE`.

**Inmutabilidad de `unit_price`:** trigger `BEFORE UPDATE` que rechaza cualquier cambio en esta columna. Implementa `RN-07` (precio inmutable al momento de venta) como defensa final ante errores de aplicación.

**Consistencia subtotal:** validación a nivel de servicio: `subtotal = unit_price × quantity`. No se delega a la DB para permitir descuentos manuales en el futuro sin migración.

**Índices:**
- `CREATE INDEX idx_order_items_order ON order_items(order_id);`
- `CREATE INDEX idx_order_items_product ON order_items(product_code);`

### Tabla: admin_users

| Columna        | Tipo         | Constraints                              |
|----------------|--------------|------------------------------------------|
| id             | SERIAL       | PRIMARY KEY                              |
| email          | VARCHAR(255) | NOT NULL UNIQUE                          |
| password_hash  | TEXT         | NOT NULL (bcrypt)                        |
| role           | admin_role   | NOT NULL DEFAULT 'staff'                 |
| is_active      | BOOLEAN      | NOT NULL DEFAULT TRUE                    |
| created_at     | TIMESTAMPTZ  | NOT NULL DEFAULT NOW()                   |

**Seed inicial obligatorio:** crear un usuario `admin` con contraseña temporal generada en deploy. La contraseña se cambia en el primer login.

**Índices:** `CREATE INDEX idx_admin_users_email ON admin_users(email) WHERE is_active = TRUE;`

### Triggers de inmutabilidad

```sql
-- Bloquea cambios a unit_price en order_items (RN-07)
CREATE OR REPLACE FUNCTION fn_block_unit_price_update()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.unit_price IS DISTINCT FROM OLD.unit_price THEN
    RAISE EXCEPTION 'order_items.unit_price es inmutable (RN-07)';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_block_unit_price_update
BEFORE UPDATE ON order_items
FOR EACH ROW EXECUTE FUNCTION fn_block_unit_price_update();

-- Bloquea cambios a total_amount en orders después de creación
CREATE OR REPLACE FUNCTION fn_block_total_amount_update()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.total_amount IS DISTINCT FROM OLD.total_amount THEN
    RAISE EXCEPTION 'orders.total_amount es inmutable (RN-07)';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_block_total_amount_update
BEFORE UPDATE ON orders
FOR EACH ROW EXECUTE FUNCTION fn_block_total_amount_update();
```

---

## SECCIÓN 3 — ENDPOINTS REST DE LA API

**Convenciones:**
- Base URL pública: `/api/v1/`
- Base URL admin: `/api/v1/admin/`
- Autenticación admin: header `Authorization: Bearer <jwt>`
- Formato JSON. Fechas en ISO 8601 UTC.
- Errores: `{ "error": { "code": "STR", "message": "STR", "details": {} } }`

| Método | Ruta                                  | Rol requerido     | Descripción                                                  | Body / Response |
|--------|---------------------------------------|-------------------|--------------------------------------------------------------|------------------|
| GET    | /products                             | Público           | Lista paginada de productos activos con filtros              | `?page&per_page&category&search` → `{ data: [...], pagination }` |
| GET    | /products/:code                       | Público           | Detalle por código                                           | — → Product |
| GET    | /products/slug/:slug                  | Público           | Detalle por slug                                             | — → Product |
| GET    | /categories                           | Público           | Lista de categorías                                          | — → `[{ id, name, slug }]` |
| POST   | /customers                            | Público           | Registra cliente sin login                                   | `{ name, email, phone?, address? }` → Customer |
| POST   | /orders                               | Público           | Crea pedido, valida `RN-05`                                  | `{ customer_id, items: [{ product_code, quantity }], notes? }` → Order o 422 si total < $60.000 |
| POST   | /admin/auth/login                     | Público           | Devuelve JWT y refresh token                                 | `{ email, password }` → `{ access_token, refresh_token }` |
| POST   | /admin/auth/refresh                   | Autenticado       | Renueva access token                                         | `{ refresh_token }` → `{ access_token }` |
| GET    | /admin/products                       | staff, admin      | Lista todos los productos (incluye inactivos)                | `?page&per_page&include_inactive=true` → `{ data, pagination }` |
| GET    | /admin/products/:code/exists          | staff, admin      | Validación en tiempo real del código (`RN-01`)              | — → `{ exists: boolean }` |
| POST   | /admin/products                       | staff, admin      | Crea producto, valida `RN-01`                                | `{ code, name, description?, price, stock, category_id, image_url? }` → Product o 409 si código existe |
| PUT    | /admin/products/:code                 | staff, admin      | Edita producto                                               | `{ ...campos }` → Product |
| PATCH  | /admin/products/:code/status          | staff, admin      | Activa/desactiva (`RN-02`)                                  | `{ is_active: boolean }` → Product |
| POST   | /admin/products/:code/image           | staff, admin      | Sube imagen a Cloudflare R2                                  | multipart/form-data → `{ image_url }` |
| GET    | /admin/orders                         | staff, admin      | Lista pedidos con filtros                                    | `?status&date_from&date_to&page` → `{ data, pagination }` |
| GET    | /admin/orders/:id                     | staff, admin      | Detalle de pedido con items y precios al momento de venta    | — → OrderDetail |
| PATCH  | /admin/orders/:id/status              | staff, admin      | Cambia estado (`RN-08`)                                     | `{ status }` → Order |
| GET    | /admin/analytics/*                    | admin             | **403 Forbidden en MVP** (fase 2 — flag `ANALYTICS_ENABLED`) | — → 403 |

---

## SECCIÓN 4 — ORDEN DE IMPLEMENTACIÓN

## FASE 1 — MVP (Semanas 1-5)

### T1 — Setup del monorepo npm workspaces
- **Descripción:** inicializar estructura `/apps/web`, `/apps/api`, `/packages/shared` con workspaces.
- **Archivos/módulos afectados:** `package.json` raíz, `tsconfig.base.json`, `.env.example`, `.github/workflows/ci.yml`.
- **Criterio de done:** `npm install` desde la raíz instala los 3 workspaces. `npm run build --workspaces` compila todo sin error. CI corre lint en cada PR.
- **Depende de:** ninguna.

### T2 — Schema SQL inicial y migraciones Alembic
- **Descripción:** crear todas las tablas, ENUMs, triggers de inmutabilidad e índices de la Sección 2 mediante migraciones Alembic versionadas.
- **Archivos/módulos afectados:** `apps/api/alembic/versions/001_initial_schema.py`, `002_triggers_inmutabilidad.py`, `003_seed_admin_user.py`.
- **Criterio de done:** al aplicar las 3 migraciones sobre una DB vacía, `\dt` retorna las 6 tablas esperadas. Test: un INSERT válido en `order_items` funciona, un UPDATE sobre `unit_price` falla con error específico del trigger.
- **Depende de:** T1.

### T3 — Tipos compartidos en packages/shared
- **Descripción:** definir tipos TypeScript de todas las entidades (`Product`, `Order`, `Customer`), enums (`OrderStatus`, `AdminRole`) y contratos de API.
- **Archivos/módulos afectados:** `packages/shared/src/entities/*.ts`, `enums/*.ts`, `contracts/*.ts`.
- **Criterio de done:** `import { Product, OrderStatus } from '@alcosto/shared'` funciona desde `apps/api` (vía codegen de OpenAPI) y `apps/web`.
- **Depende de:** T1.

### T4 — Conexión a PostgreSQL y repositorios base
- **Descripción:** configurar SQLAlchemy 2.0 async, crear engine, session factory, modelos ORM y repositorios CRUD básicos sin lógica de negocio.
- **Archivos/módulos afectados:** `apps/api/app/database.py`, `app/models/*.py`, `app/repositories/*.py`.
- **Criterio de done:** test de integración con `testcontainers` que inserta un producto y lo lee pasa verde.
- **Depende de:** T2, T3.

### T5 — Módulo Auth: login con JWT
- **Descripción:** endpoints `/admin/auth/login`, `/admin/auth/refresh`. Bcrypt cost 12. Access token 1h, refresh token 7 días con rotación.
- **Archivos/módulos afectados:** `apps/api/app/routers/admin/auth.py`, `app/services/auth_service.py`, `app/core/security.py`.
- **Criterio de done:** (a) login con credenciales válidas devuelve tokens; (b) refresh genera un nuevo access token e invalida el refresh anterior; (c) request a endpoint protegido sin token devuelve 401.
- **Depende de:** T4.

### T6 — Middleware de autorización por rol
- **Descripción:** dependency injection que valida JWT y rol requerido por endpoint.
- **Archivos/módulos afectados:** `apps/api/app/core/deps.py`.
- **Criterio de done:** un usuario `staff` no puede acceder a endpoints reservados a `admin`. Devuelve 403 con error específico.
- **Depende de:** T5.

### T7 — Módulo Productos: CRUD admin
- **Descripción:** endpoints `/admin/products` (GET, POST, PUT, PATCH status). Implementa validación `RN-01` (código único manual) en el service y verificación tiempo real con `/exists`.
- **Archivos/módulos afectados:** `apps/api/app/routers/admin/products.py`, `app/services/product_service.py`, `app/repositories/product_repo.py`.
- **Criterio de done:** (a) crear producto con código nuevo → 201; (b) crear producto con código duplicado → 409 con mensaje "código ya existe"; (c) endpoint `/exists` retorna `{exists: true/false}` correctamente; (d) `PATCH /status {is_active: false}` desactiva pero `GET /admin/products?include_inactive=true` lo sigue mostrando; (e) intento de DELETE físico de producto con order_items asociados falla con error de FK.
- **Depende de:** T4, T6.

### T8 — Módulo Productos: catálogo público
- **Descripción:** endpoints `/products`, `/products/:code`, `/products/slug/:slug`, `/categories`. Solo retorna productos con `is_active = TRUE`. Soporta paginación cursor-based, filtro por categoría y búsqueda por nombre (full-text PostgreSQL).
- **Archivos/módulos afectados:** `apps/api/app/routers/public/products.py`, `app/routers/public/categories.py`.
- **Criterio de done:** (a) un producto con `is_active=false` no aparece en `GET /products` ni en `GET /products/:code` (404); (b) búsqueda por `?search=xxx` retorna productos cuyo nombre contiene el texto; (c) filtro `?category=slug` retorna solo productos de esa categoría; (d) paginación con `next_cursor` no salta ni duplica registros.
- **Depende de:** T7.

### T9 — Módulo Pedidos: creación con validación de mínimo y snapshots de precio
- **Descripción:** `POST /orders` ejecuta transacción atómica: valida total ≥ $60.000 (`RN-05`), crea registro de cliente si es nuevo, copia precio actual de cada producto a `order_items.unit_price` (`RN-07`), calcula subtotales y total, persiste todo o nada.
- **Archivos/módulos afectados:** `apps/api/app/routers/public/orders.py`, `app/services/order_service.py`, `app/repositories/order_repo.py`.
- **Criterio de done:** (a) pedido con total ≥ $60.000 se crea exitosamente y retorna número de orden; (b) pedido con total < $60.000 retorna 422 con mensaje específico, no persiste nada; (c) si se crea un pedido y luego cambia el `price` del producto, `GET /admin/orders/:id` sigue mostrando el `unit_price` original; (d) si un producto del pedido está `is_active=false`, retorna 422; (e) test de concurrencia: dos requests simultáneos con stock = 1 producen exactamente un 201 y un 422 (sin oversell).
- **Depende de:** T7.

### T10 — Módulo Pedidos: gestión admin
- **Descripción:** `GET /admin/orders` (listado con filtros), `GET /admin/orders/:id` (detalle), `PATCH /admin/orders/:id/status` (cambio de estado).
- **Archivos/módulos afectados:** `apps/api/app/routers/admin/orders.py`, `app/services/order_service.py` (extiende T9).
- **Criterio de done:** (a) admin puede listar pedidos filtrando por estado y rango de fechas; (b) detalle muestra items con precios al momento de venta; (c) transiciones de estado válidas: `pending → confirmed → dispatched`, `pending → cancelled`, `confirmed → cancelled`. Otras transiciones retornan 409.
- **Depende de:** T9.

### T11 — Upload de imágenes a Cloudflare R2
- **Descripción:** endpoint `POST /admin/products/:code/image`. Cliente boto3 hacia R2, validación de tipo MIME y tamaño máximo (5MB), generación de URL pública.
- **Archivos/módulos afectados:** `apps/api/app/routers/admin/products.py` (extiende T7), `app/services/storage_service.py`, `app/config.py`.
- **Criterio de done:** (a) upload de PNG/JPG válido retorna URL pública accesible; (b) archivo > 5MB retorna 413; (c) tipo MIME no soportado retorna 415; (d) la URL guardada en `products.image_url` se sirve correctamente desde el catálogo.
- **Depende de:** T7.

### T12 — Script de migración desde WordPress
- **Descripción:** script Python único que conecta a WPGraphQL del WordPress existente, extrae todos los productos paginados, separa el código numérico del campo descripción (donde el operador lo guardó), conserva URLs de imágenes originales, resuelve categorías. Implementa `RN-12` y `RN-13`.
- **Archivos/módulos afectados:** `apps/api/scripts/migrate_from_wordpress.py`.
- **Criterio de done:** (a) ejecución única migra el 100% de productos válidos; (b) imprime resumen final con: total migrados, omitidos por código duplicado, errores con detalle; (c) productos sin código numérico válido se registran en log de errores y NO se importan; (d) `GET /products` retorna los productos migrados con sus imágenes funcionando desde URLs originales de WordPress.
- **Depende de:** T7.

### T13 — Setup Next.js, Tailwind y design tokens
- **Descripción:** app Next.js 14 con App Router, Tailwind con tokens de marca AlCosto (azul #1B3FA0, rojo #C8181E, amarillo #F5C400, gris #8A8A8A, fondo #F8F8F8) según `RN-09`.
- **Archivos/módulos afectados:** `apps/web/tailwind.config.ts`, `app/layout.tsx`, `styles/globals.css`.
- **Criterio de done:** una página de prueba renderiza `bg-brand-bg text-brand-blue` y aplica los colores exactos. El logo AlCosto aparece en el navbar.
- **Depende de:** T1.

### T14 — Componentes atómicos UI
- **Descripción:** los 10 componentes de la Sección 5B.
- **Archivos/módulos afectados:** `apps/web/components/atoms/*.tsx`.
- **Criterio de done:** página `/dev/components` que renderiza los 10 componentes con props válidos. Todos pasan tests con React Testing Library.
- **Depende de:** T13.

### T15 — Cliente HTTP del frontend con manejo de JWT
- **Descripción:** wrapper sobre fetch con manejo automático de Authorization header, refresh transparente en 401, redirect a login en refresh fallido.
- **Archivos/módulos afectados:** `apps/web/lib/api-client.ts`.
- **Criterio de done:** (a) request con token expirado refresca automáticamente y reintenta; (b) refresh fallido limpia tokens y redirige a `/login`; (c) request a endpoint público no envía header.
- **Depende de:** T13.

### T16 — Catálogo público con Server Components
- **Descripción:** ruta `/` con SSR del primer batch de productos para SEO. Filtro por buscador y categoría client-side. Botón "Ver más" carga siguiente página sin recargar. Implementa criterios de "Catálogo público" del SPEC.
- **Archivos/módulos afectados:** `apps/web/app/(public)/page.tsx`, `modules/catalog/components/*`, `modules/catalog/services/api.ts`.
- **Criterio de done:** (a) la primera carga incluye productos en el HTML inicial (verificable con `view-source`); (b) "Ver más" agrega productos sin recargar la página; (c) buscador filtra los productos ya descargados en cliente; (d) el badge `COD: XXX` aparece en cada card con fondo amarillo y texto azul (`RN-04`, `RN-11`).
- **Depende de:** T8, T14.

### T17 — Detalle de producto
- **Descripción:** ruta `/productos/[slug]` con SSR. Incluye imagen, descripción completa, precio, badge COD, botón "Agregar al carrito".
- **Archivos/módulos afectados:** `apps/web/app/(public)/productos/[slug]/page.tsx`.
- **Criterio de done:** producto con `is_active=false` retorna 404. La URL es indexable por buscadores (meta tags OK).
- **Depende de:** T16.

### T18 — Carrito con Zustand y validación de mínimo
- **Descripción:** store con persistencia en localStorage. Componente `<CartProgress>` que muestra barra hacia $60.000. Botón confirmar deshabilitado bajo el mínimo (`RN-05`, `RN-06`).
- **Archivos/módulos afectados:** `apps/web/modules/cart/store.ts`, `components/CartProgress.tsx`, `app/(public)/carrito/page.tsx`.
- **Criterio de done:** (a) agregar producto al carrito persiste tras refresh; (b) total < $60.000: barra muestra progreso, botón "Confirmar" no aparece; (c) total ≥ $60.000: barra completa, botón visible y habilitado; (d) el mensaje "te faltan $X" se actualiza en tiempo real.
- **Depende de:** T14.

### T19 — Checkout y creación de pedido
- **Descripción:** formulario de cliente (nombre, teléfono, dirección, notas), resumen del pedido, confirmación. Pega a `POST /orders`.
- **Archivos/módulos afectados:** `apps/web/app/(public)/carrito/checkout/page.tsx`, `modules/checkout/components/*`.
- **Criterio de done:** flujo end-to-end: cliente completa form, confirma, recibe número de pedido, carrito se vacía. Verificar que el pedido aparece en `/admin/pedidos`.
- **Depende de:** T18, T9.

### T20 — Pantalla de login admin
- **Descripción:** ruta `/login` con formulario email/password. Pega a `POST /admin/auth/login`.
- **Archivos/módulos afectados:** `apps/web/app/(admin)/login/page.tsx`, `middleware.ts` (protección de `/admin/*`).
- **Criterio de done:** (a) login exitoso redirige a `/admin/productos`; (b) login fallido muestra mensaje genérico ("credenciales inválidas"); (c) acceso directo a `/admin/*` sin sesión redirige a `/login`.
- **Depende de:** T15, T5.

### T21 — Panel admin: listado y formulario de productos
- **Descripción:** ruta `/admin/productos` con tabla. Ruta `/admin/productos/nuevo` y `/admin/productos/[code]/editar` con formulario unificado. Validación tiempo real del código vía `/exists`.
- **Archivos/módulos afectados:** `apps/web/app/(admin)/admin/productos/*`, `modules/admin-products/*`.
- **Criterio de done:** (a) operador carga producto con código nuevo → guarda OK; (b) intento con código existente muestra error inline antes de submit; (c) toggle activo/inactivo en el listado funciona sin recargar; (d) edición preserva todos los campos al guardar; (e) upload de imagen funciona y se previsualiza.
- **Depende de:** T7, T11, T20.

### T22 — Panel admin: gestión de pedidos
- **Descripción:** ruta `/admin/pedidos` con tabla, filtros (estado, fecha) y vista de detalle. Cambio de estado inline.
- **Archivos/módulos afectados:** `apps/web/app/(admin)/admin/pedidos/*`.
- **Criterio de done:** (a) tabla muestra todos los pedidos con paginación; (b) filtros por estado y fecha funcionan; (c) vista de detalle muestra items con precios al momento de la venta; (d) cambio de estado se refleja inmediatamente.
- **Depende de:** T10, T20.

### T23 — Suite de tests críticos consolidada
- **Descripción:** consolidar y ejecutar en CI los tests que validan reglas de negocio críticas: `RN-01` (código único), `RN-02` (no borrado físico), `RN-05` (mínimo $60.000), `RN-07` (precio inmutable). E2E con Playwright para flujo completo de compra.
- **Archivos/módulos afectados:** `apps/api/tests/test_rn_critical.py`, `apps/web/tests/e2e/checkout.spec.ts`, `.github/workflows/ci.yml`.
- **Criterio de done:** CI bloquea merge si cualquier test crítico falla. La suite cubre 100% de las reglas de negocio del SPEC.
- **Depende de:** T9, T19, T22.

## FASE 2 — Módulo de Reportes (vendible — Semanas 6+)

Activación mediante flag `ANALYTICS_ENABLED=true`. No requiere migraciones de DB ni cambios de infraestructura.

### T24 — Endpoint y dashboard de ventas por período
- **Descripción:** `GET /admin/analytics/sales` con agrupación por día/semana/mes. Pantalla con gráfico de líneas (Recharts).
- **Criterio de done:** dashboard muestra total de ventas confirmadas en el rango seleccionado, agrupado correctamente.
- **Depende de:** T23.

### T25 — Endpoint y panel de productos más vendidos
- **Descripción:** `GET /admin/analytics/top-products` con ranking por unidades vendidas y por revenue.
- **Criterio de done:** top 10 productos visible con cantidad y monto total. Filtrable por rango de fechas.
- **Depende de:** T23.

### T26 — Endpoint y panel de clientes frecuentes
- **Descripción:** `GET /admin/analytics/frequent-customers` agrupado por cantidad de pedidos y monto total gastado.
- **Criterio de done:** lista de clientes ordenada por frecuencia con datos de contacto.
- **Depende de:** T23.

### T27 — Endpoint y métrica de ticket promedio
- **Descripción:** `GET /admin/analytics/avg-ticket` con cálculo histórico y tendencia.
- **Criterio de done:** valor visible en dashboard con comparación contra período anterior.
- **Depende de:** T23.

---

## SECCIÓN 5 — DESIGN TOKENS Y COMPONENTES UI BASE

### A) Configuración de Tailwind

```typescript
// apps/web/tailwind.config.ts
import type { Config } from 'tailwindcss';

export default {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './modules/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          blue:   '#1B3FA0',  // RN-09: primario
          red:    '#C8181E',  // RN-09: acentos, alertas
          yellow: '#F5C400',  // RN-09: badge COD, highlights
          gray:   '#8A8A8A',  // RN-09: textos secundarios
          bg:     '#F8F8F8',  // RN-09: fondo general
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config;
```

### B) Componentes atómicos

| # | Nombre              | Props principales                                                                       | Pantalla donde se usa primero |
|---|---------------------|------------------------------------------------------------------------------------------|-------------------------------|
| 1 | `<CodBadge />`      | `code: number`                                                                           | `/` (catálogo)                |
| 2 | `<ProductCard />`   | `product: Product`, `onAddToCart?: () => void`                                          | `/` (catálogo)                |
| 3 | `<CartProgress />`  | `current: number`, `min: number = 60000`                                                | `/carrito`                    |
| 4 | `<CategoryFilter/>` | `categories: Category[]`, `selected?: string`, `onChange: (slug: string) => void`       | `/` (catálogo)                |
| 5 | `<SearchBar />`     | `value: string`, `onChange: (text: string) => void`, `placeholder?: string`             | `/` (catálogo)                |
| 6 | `<Button />`        | `variant: 'primary'\|'secondary'\|'danger'`, `size?: 'sm'\|'md'\|'lg'`, `loading?: bool`| transversal                   |
| 7 | `<InputField />`    | `label: string`, `value: string`, `onChange`, `error?: string`, `type?: string`         | `/login`, formularios admin   |
| 8 | `<DataTable />`     | `columns: Column[]`, `rows: Row[]`, `onRowClick?: (row) => void`                        | `/admin/productos`, `/admin/pedidos` |
| 9 | `<StatusBadge />`   | `status: OrderStatus`                                                                    | `/admin/pedidos`              |
| 10 | `<Toast />`        | `type: 'success'\|'error'\|'info'`, `message: string`, `duration?: number`              | transversal                   |

---

## SECCIÓN 6 — DECISIONES ARQUITECTÓNICAS

**DECISIÓN:** Backend en FastAPI (Python) en lugar de NestJS o Express.  
**Alternativa descartada:** NestJS (Node.js) con TypeORM.  
**Justificación:** El proyecto tiene 100-500 productos y 1-2 operadores concurrentes; NestJS arrastra una complejidad de configuración (decoradores, módulos, DI) pensada para equipos grandes. Express, por el contrario, es demasiado minimalista y obliga a tomar 20 decisiones que FastAPI ya tomó: documentación OpenAPI automática, validación con Pydantic v2, integración nativa con Alembic, serialización async. Para un MVP de un solo desarrollador, FastAPI minimiza el boilerplate sin sacrificar capacidad de escalar.

**DECISIÓN:** PostgreSQL como base de datos en lugar de MongoDB u otra NoSQL.  
**Alternativa descartada:** MongoDB con Mongoose.  
**Justificación:** El módulo de reportes (fase 2 vendible) depende de joins entre `orders`, `order_items`, `products` y `categories`. En SQL eso es un `GROUP BY` directo; en MongoDB requiere aggregation pipelines complejas. Además, los CHECK constraints, las foreign keys con `RESTRICT` y los triggers de inmutabilidad son la única forma robusta de implementar `RN-02` y `RN-07` a nivel físico. Sin esa defensa, cualquier bug de aplicación puede romper la integridad histórica.

**DECISIÓN:** `products.code` como `INTEGER PRIMARY KEY` asignado manualmente, no `SERIAL` autoincremental.  
**Alternativa descartada:** UUID o SERIAL como PK + columna `external_code` para el código del sistema externo.  
**Justificación:** El SPEC `RN-01` declara que el código viene de un sistema externo del operador (remitos, facturas) y debe coincidir con él. Tener dos identificadores (uno interno, uno externo) introduce ambigüedad: ¿cuál se usa en logs, en URLs, en reportes? Usar el código externo como PK fuerza coherencia entre AlCosto y el sistema fuente. La validación de unicidad antes del INSERT es trivial; el único costo es la validación en tiempo real durante la carga, que ya es un requisito de UX (`/admin/products/{code}/exists`).

**DECISIÓN:** Soft delete obligatorio en `products` mediante columna `is_active`. La FK `order_items.product_code` usa `ON DELETE RESTRICT`.  
**Alternativa descartada:** Hard delete con `ON DELETE CASCADE` o tabla `products_archived` separada.  
**Justificación:** `RN-02` exige preservar el historial de pedidos. `CASCADE` borraría los `order_items` junto al producto, destruyendo data crítica para reportes. Una tabla `products_archived` agrega complejidad de migración cada vez que un producto cambia de estado y duplica la lógica de búsqueda. La columna `is_active` con índice parcial (`WHERE is_active = TRUE`) es la solución más simple y robusta.

**DECISIÓN:** `order_items.unit_price` se copia al momento de la venta y se protege con trigger `BEFORE UPDATE`.  
**Alternativa descartada:** Calcular el precio al vuelo desde `products.price` cada vez que se consulta el pedido.  
**Justificación:** `RN-07` declara el precio inmutable. Recalcular al vuelo produciría totales distintos a lo que pagó el cliente, rompiendo la trazabilidad y dejando el sistema vulnerable a disputas. El trigger es defensa final ante errores de aplicación: aunque un bug intente actualizar el precio, la DB lo rechaza.

**DECISIÓN:** Mínimo de compra `$60.000` validado en tres capas: frontend (UX), service (lógica), CHECK constraint en DB.  
**Alternativa descartada:** Validación solo en frontend o solo en backend.  
**Justificación:** El frontend valida para UX (mostrar progreso, deshabilitar botón). El service valida porque un cliente malicioso puede pegar a `POST /orders` directamente bypaseando el frontend. El CHECK en DB es la última defensa: si por bug futuro se modifica el service, la DB sigue protegiendo la regla. Tres capas para una regla que genera ingresos del negocio es paranoia justificada.

**DECISIÓN:** API REST FastAPI desacoplada del frontend Next.js, en monorepo con workspace npm.  
**Alternativa descartada:** Next.js fullstack con API Routes en el mismo deploy.  
**Justificación:** El módulo de reportes (fase 2) y eventuales clientes futuros (app mobile, integración con sistema de stock externo del operador) requieren una API REST autónoma. Empezar con API Routes implicaría migrar todo el backend cuando llegue el segundo cliente. El costo extra de desplegar dos servicios (Vercel para frontend, Railway para backend) es marginal frente al refactor evitado.

**DECISIÓN:** Imágenes legacy de WordPress se conservan por URL; imágenes nuevas se suben a Cloudflare R2.  
**Alternativa descartada:** Migrar todas las imágenes a R2 en el lanzamiento.  
**Justificación:** `RN-13` exige cero fricción para el operador en el lanzamiento. WordPress sigue activo sin fecha de cierre. Migrar 100-500 imágenes en el día 1 introduce riesgo (imágenes rotas, formatos no compatibles) sin beneficio inmediato. La estrategia gradual: cualquier producto nuevo o editado migra su imagen a R2 automáticamente; en 3-6 meses la mayoría del catálogo ya está en R2 sin que nadie lo note. Cuando WordPress deba darse de baja, un script secundario migra los rezagados.

**DECISIÓN:** El router `/admin/analytics/*` existe en el código del MVP pero retorna 403 Forbidden mientras `ANALYTICS_ENABLED=false`.  
**Alternativa descartada:** Construir el módulo de analytics solo en la fase 2.  
**Justificación:** La activación del módulo (cuando se le venda al operador) debe ser un cambio de configuración, no un deploy de código nuevo con migraciones. La data necesaria para reportes (`order_items.unit_price`, `orders.created_at`, FK a productos) ya se acumula desde el día 1 gracias a las decisiones de modelo de datos. Cambiar el flag activa instantáneamente el acceso a endpoints que ya están funcionando, solo bloqueados.

**DECISIÓN:** JWT con access token de 1h y refresh token de 7 días con rotación, en lugar de cookies httpOnly.  
**Alternativa descartada:** Cookie httpOnly de 8 horas como mecanismo único.  
**Justificación:** A diferencia de un sistema interno con tablets fijas, AlCosto puede acceder desde múltiples dispositivos del operador (notebook personal, móvil para revisar pedidos en la calle). El refresh token con rotación permite sesiones largas con tokens de corta vida; la rotación detecta tokens robados. La cookie httpOnly se evaluará si en el futuro se identifica un vector XSS específico que el JWT no cubra.

---

## SECCIÓN 7 — TRAZABILIDAD SPEC → PLAN

| Regla SPEC | Implementación en PLAN |
|------------|------------------------|
| `RN-01` Código manual único | PK manual `INTEGER` + endpoint `/exists` (T7) + validación service + UNIQUE implícito de PK |
| `RN-02` Soft delete obligatorio | Columna `is_active` + FK `order_items.product_code` con `ON DELETE RESTRICT` (T2, T7) |
| `RN-03` Campos del producto | Esquema SQL `products` + Pydantic schema (T2, T3) |
| `RN-04` Badge COD visible | Componente `<CodBadge />` (T14) usado en `<ProductCard />` y detalle |
| `RN-05` Mínimo $60.000 | Validación 3 capas: `<CartProgress>` (T18) + service `order_service.create()` (T9) + CHECK constraint (T2) |
| `RN-06` Bloqueo de confirmación | `<CartProgress>` con botón condicional (T18) |
| `RN-07` Precio inmutable | Columna `order_items.unit_price` separada + trigger `fn_block_unit_price_update` (T2) |
| `RN-08` Estados de pedido | ENUM `order_status` + validación de transiciones en service (T10) |
| `RN-09`, `RN-10`, `RN-11` Identidad visual | Tokens en `tailwind.config.ts` (T13) + componentes que los consumen |
| `RN-12` Migración sin intervención | Script `migrate_from_wordpress.py` (T12) |
| `RN-13` URLs de WordPress preservadas | Mapeo directo en script de migración a `products.image_url` (T12) |

---

## SECCIÓN 8 — ESTRATEGIA DE TESTING

### Backend (apps/api/tests/)
- **Unit tests** sobre `services/` con mocks de repositorios. Cobertura mínima: 100% de reglas de negocio.
- **Integration tests** con `pytest` + `testcontainers` (PostgreSQL real en Docker) sobre routers.
- **Tests críticos obligatorios** (incluidos en T23, bloquean merge en CI):
  - `test_rn01_codigo_unique`: rechazo de código duplicado en `POST /admin/products`.
  - `test_rn02_no_hard_delete`: imposibilidad de borrado físico cuando hay `order_items` asociados.
  - `test_rn05_minimum_amount`: rechazo de pedido bajo $60.000 en service y en DB.
  - `test_rn07_unit_price_immutable`: trigger bloquea UPDATE sobre `unit_price`.
  - `test_rn07_price_change_doesnt_affect_history`: cambiar `products.price` no modifica `order_items.unit_price` de pedidos previos.

### Frontend (apps/web/tests/)
- **Unit tests** con Vitest sobre utilidades del carrito (cálculo total, validación mínimo).
- **Component tests** con React Testing Library para `<CodBadge>`, `<ProductCard>`, `<CartProgress>`.
- **E2E con Playwright** (incluido en T23):
  - Flujo completo de compra: navegar catálogo → agregar productos → llegar a $60.000 → confirmar → ver número de pedido.
  - Login admin → cargar producto nuevo → ver en catálogo público.

---

## SECCIÓN 9 — PLAN DE DESPLIEGUE

### Entornos
| Entorno   | Frontend                | Backend                | DB                        |
|-----------|-------------------------|------------------------|---------------------------|
| Local     | `localhost:3000`        | `localhost:8000`       | Docker compose PostgreSQL |
| Staging   | Vercel preview          | Railway preview env    | Railway PostgreSQL preview|
| Producción| Vercel production       | Railway production     | Railway PostgreSQL prod   |

### CI/CD
- GitHub Actions corre lint + tests críticos en cada PR.
- Merge a `main` → deploy automático: Vercel para frontend, Railway para backend.
- Migraciones Alembic se ejecutan en el paso de deploy del backend, antes de levantar la nueva versión.

### Variables de entorno requeridas

**Frontend (`apps/web/.env`):**
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_R2_PUBLIC_URL`

**Backend (`apps/api/.env`):**
- `DATABASE_URL`
- `JWT_SECRET`
- `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET`, `R2_ENDPOINT`
- `ALLOWED_ORIGINS`
- `ANALYTICS_ENABLED` (default: `false`)
- `WORDPRESS_GRAPHQL_URL` (solo para script de migración inicial)

---

*Este plan deriva del SPEC.md v2.0 y es la única fuente de verdad técnica del proyecto. Cualquier cambio en las reglas de negocio del SPEC debe propagarse a este documento. La siguiente etapa SDD es el desarrollo guiado por las tareas T1–T23, donde cada una se implementa en una sesión limpia de Claude con su criterio de done como contrato verificable.*