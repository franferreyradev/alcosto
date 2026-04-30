# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: AlCosto — Plataforma Mayorista B2B

Monorepo con npm workspaces. Frontend Next.js 14, backend FastAPI (Python), tipos compartidos en TypeScript. Deployed en Vercel (frontend) + Railway (backend + PostgreSQL).

---

## Commands

### Root (monorepo)
```bash
npm install                          # instala los 3 workspaces
npm run build --workspaces           # compila todo
npm run lint --workspaces            # lint en todos los workspaces
```

### Frontend — apps/web
```bash
npm run dev --workspace=apps/web     # dev server en localhost:3000
npm run build --workspace=apps/web
npm run test --workspace=apps/web    # Vitest unit + React Testing Library
npx playwright test                  # E2E (desde apps/web/)
```

### Backend — apps/api
```bash
# Desde apps/api/
uvicorn app.main:app --reload        # dev server en localhost:8000
pytest                               # todos los tests
pytest tests/test_rn_critical.py    # solo tests críticos (bloquean CI)
pytest -k "test_name"                # test individual

alembic upgrade head                 # aplicar migraciones
alembic revision --autogenerate -m "descripción"  # nueva migración

python scripts/migrate_from_wordpress.py  # migración inicial (uso único)
```

### Docker local
```bash
docker compose up -d                 # PostgreSQL en local
```

---

## Architecture

### Monorepo structure
```
alcosto/
├── apps/web/          → Next.js 14 App Router (catálogo público + panel admin)
├── apps/api/          → FastAPI backend (API REST desacoplada)
└── packages/shared/   → Tipos TypeScript compartidos entre web y api (codegen OpenAPI)
```

### apps/api — FastAPI
Capas estrictas sin mezcla:
- `routers/` — orquestan request/response únicamente; no contienen lógica de negocio
- `services/` — lógica de negocio pura, testeable en aislamiento con mocks de repos
- `repositories/` — queries SQL y transacciones; sin lógica de negocio
- `models/` — SQLAlchemy ORM
- `schemas/` — DTOs Pydantic v2 (nunca se mezclan con modelos ORM)
- `core/` — auth, deps, security, exceptions

Endpoints agrupados en `routers/public/` (sin auth) y `routers/admin/` (JWT requerido).

### apps/web — Next.js 14
- Server Components por defecto. `"use client"` solo cuando hay interactividad real.
- Módulos de dominio en `modules/` (catalog, cart, admin-products, etc.): cada módulo es independiente y no importa de otros módulos directamente. Se comunican vía `packages/shared/` o vía API.
- Componentes atómicos en `components/atoms/`.
- Cliente HTTP con auto-refresh de JWT en `lib/api-client.ts`.
- Estado del carrito con Zustand + persistencia en localStorage.

### packages/shared
Tipos del dominio (`Product`, `Order`, `Customer`), enums (`OrderStatus`, `AdminRole`) y contratos de API. Se genera desde OpenAPI del backend.

---

## Database

PostgreSQL. Migraciones con Alembic (versionadas en `apps/api/alembic/versions/`).

`products.code` es `INTEGER PRIMARY KEY` asignado manualmente por el operador (no SERIAL/UUID). Viene de un sistema externo de remitos/facturas.

**Triggers de inmutabilidad (no saltear):**
- `trg_block_unit_price_update` — bloquea cualquier UPDATE a `order_items.unit_price` (RN-07)
- `trg_block_total_amount_update` — bloquea cualquier UPDATE a `orders.total_amount` (RN-07)

**Soft delete obligatorio en `products`:** columna `is_active`. La FK `order_items.product_code ON DELETE RESTRICT` impide borrado físico. Nunca hacer hard delete de productos.

---

## Business Rules (invariantes — ninguna decisión técnica puede contradirlas)

| Regla | Descripción |
|-------|-------------|
| `RN-01` | Código de producto: numérico, asignado manualmente por el operador, único. Endpoint `/admin/products/{code}/exists` para validación en tiempo real. |
| `RN-02` | Soft delete obligatorio. Un producto nunca se borra físicamente. Solo `is_active = FALSE`. |
| `RN-05` | Mínimo de pedido: **$60.000**. Validado en 3 capas: frontend (UX), service, y CHECK constraint en DB. |
| `RN-07` | Precio de ítem al momento de la venta es inmutable. `order_items.unit_price` se copia del producto en el momento del pedido y no puede cambiar después. |
| `RN-08` | Transiciones de estado válidas: `pending → confirmed → dispatched`, `pending → cancelled`, `confirmed → cancelled`. Cualquier otra retorna 409. |

---

## Auth

JWT: access token 1h, refresh token 7 días con rotación. Header `Authorization: Bearer <jwt>`.

Roles: `admin` (acceso total) y `staff` (acceso a productos y pedidos, sin analytics ni gestión de usuarios).

`/admin/analytics/*` retorna 403 en MVP mientras `ANALYTICS_ENABLED=false`.

---

## Brand / Design Tokens

```
azul:     #1B3FA0  (primario, texto de badge COD)
rojo:     #C8181E  (acentos, alertas)
amarillo: #F5C400  (fondo de badge COD)
gris:     #8A8A8A  (textos secundarios)
fondo:    #F8F8F8
```

Configurados en `apps/web/tailwind.config.ts` como `brand.blue`, `brand.red`, `brand.yellow`, `brand.gray`, `brand.bg`.

---

## Testing Strategy

**Backend (pytest + testcontainers):**
- Unit tests sobre `services/` con mocks de repositorios.
- Integration tests con PostgreSQL real vía `testcontainers`.
- Tests críticos en `tests/test_rn_critical.py` — bloquean merge en CI.

**Frontend:**
- Vitest para utilidades (cálculo de carrito, validación de mínimo).
- React Testing Library para componentes atómicos.
- Playwright E2E: flujo completo de compra + login admin.

---

## Environments & Deploy

| Entorno    | Frontend        | Backend             | DB                        |
|------------|-----------------|---------------------|---------------------------|
| Local      | localhost:3000  | localhost:8000      | Docker compose PostgreSQL |
| Staging    | Vercel preview  | Railway preview     | Railway PostgreSQL preview|
| Producción | Vercel prod     | Railway prod        | Railway PostgreSQL prod   |

Merge a `main` → deploy automático. Migraciones Alembic se ejecutan en el paso de deploy del backend antes de levantar la nueva versión.

### Required env vars

**apps/web/.env:**
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_R2_PUBLIC_URL`

**apps/api/.env:**
- `DATABASE_URL`, `JWT_SECRET`
- `R2_ACCESS_KEY`, `R2_SECRET_KEY`, `R2_BUCKET`, `R2_ENDPOINT`
- `ALLOWED_ORIGINS`
- `ANALYTICS_ENABLED` (default: `false`)
- `WORDPRESS_GRAPHQL_URL` (solo para script de migración inicial)

---

## Implementation Order (MVP — Phases T1–T23)

Las tareas están documentadas en `docs/PLAN.md` Sección 4, con criterios de done verificables. El orden de dependencias es:

`T1 (monorepo setup) → T2 (DB schema) + T3 (shared types) → T4 (repos) → T5-T6 (auth) → T7-T12 (productos + pedidos API) → T13-T22 (frontend) → T23 (CI tests)`

La Fase 2 (analytics, T24-T27) se activa con `ANALYTICS_ENABLED=true` sin migraciones ni refactors.

---

## Git Workflow — OBLIGATORIO por tarea

### Antes de empezar cualquier tarea
```bash
git checkout main
git pull origin main
git checkout -b task/T[N]-[nombre-corto]
# Ejemplo: task/T7-crud-productos
```

### Durante la tarea
Commitear cada unidad lógica terminada, no todo al final:
```bash
git add <archivos específicos>
git commit -m "[tipo]: [descripción en español]"
# feat: router de productos con validación RN-01
# feat: repositorio base con CRUD
# test: integración — insert y código duplicado pasan verde
```

### Cuando el criterio de done está verificado
```bash
git add <archivos específicos>
git commit -m "feat: T[N] completa — [nombre exacto del PLAN.md]"
git push origin task/T[N]-[nombre-corto]

gh pr create \
  --title "T[N]: [nombre exacto del PLAN.md]" \
  --body "## Tarea completada
- Criterio de done: verificado ✓
- Comando ejecutado: [comando real y output]
- Archivos modificados: [lista]

## Decisiones locales
[Si hubo alguna. Si no: 'Ninguna.']

## Checklist
- [ ] Tests pasan
- [ ] No se modificó ninguna zona prohibida
- [ ] handoff-actual.md actualizado" \
  --base main
```

### Nunca hacer
- `git push origin main` directo
- Commitear en `main` sin PR
- Mergear sin haber verificado el criterio de done
- Usar `--no-verify` para saltear hooks

---

## Handoff por sesión — OBLIGATORIO al cerrar

Al terminar cualquier tarea, sobreescribir `docs/handoff-actual.md` con:

```markdown
## HANDOFF — [FECHA] — [ID Tarea completada]

### Tarea completada
- ID y nombre (del PLAN.md):
- Archivos creados/modificados: (ruta → qué hace)
- Criterio de done verificado: sí / parcial → detalle
- Comando de verificación ejecutado y resultado:

### Decisiones locales tomadas
- [Si no estaba en PLAN ni SPEC] → razón

### Problemas conocidos
- [Deuda técnica o comportamiento raro] → impacto esperado

### Tarea siguiente
- ID y nombre:
- Depende de: ✓ resuelta
- Primer paso concreto:
- Archivos a leer primero:
```

---

## Cuándo escalar al desarrollador — no continuar solo

- El criterio de done requiere más de 3 intentos sin pasar.
- La solución requiere modificar una zona prohibida (triggers de inmutabilidad, lógica de RN-07, schema de DB sin migración Alembic).
- Conflicto entre SPEC y PLAN sin resolución obvia.
- Dependencia externa (Railway, Cloudflare R2, WordPress GraphQL) no responde como define el PLAN.
