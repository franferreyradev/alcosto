## HANDOFF — 2026-04-30 — T1 Setup del monorepo npm workspaces

### Tarea completada
- ID y nombre: T1 — Setup del monorepo npm workspaces
- Archivos creados/modificados:
  - `package.json` → raíz del monorepo, npm workspaces (apps/web, apps/api, packages/shared)
  - `tsconfig.base.json` → config TypeScript base compartida (strict, ES2022, bundler)
  - `README.md` → actualizado con instrucciones de setup correctas (Python 3.12, rutas reales)
  - `.github/workflows/ci.yml` → lint + build en cada PR y push
  - `apps/web/package.json` → workspace Next.js 14, depende de @alcosto/shared
  - `apps/web/tsconfig.json` → extiende base, plugins next, paths @/*
  - `apps/web/next.config.js` → transpilePackages shared
  - `apps/web/.eslintrc.json` → extends next/core-web-vitals
  - `apps/web/app/layout.tsx` → root layout mínimo
  - `apps/web/app/page.tsx` → placeholder (se reemplaza en T16)
  - `apps/api/pyproject.toml` → deps FastAPI, SQLAlchemy, Alembic, pydantic-settings, testcontainers
  - `apps/api/app/main.py` → FastAPI app, CORS, endpoint /health
  - `apps/api/app/config.py` → Settings pydantic-settings con todas las vars de entorno
  - `apps/api/Dockerfile` → multi-stage para Railway
  - `packages/shared/package.json` → workspace @alcosto/shared
  - `packages/shared/tsconfig.json` → extiende base, emite declaraciones
  - `packages/shared/src/index.ts` → barrel vacío (se completa en T3)
  - Directorios vacíos con .gitkeep: components, modules, lib, public, styles (web), routers/public, routers/admin, services, repositories, models, schemas, core, alembic/versions, scripts, tests (api), entities, enums, contracts (shared), docs/adr
- Criterio de done verificado: **sí**
  - `npm install` → 390 packages, sin errores
  - `npm run build --workspaces --if-present` → Next.js + tsc shared compilados sin errores
  - `npm run lint --workspaces --if-present` → sin warnings ni errores
- Comando de verificación: `npm run build --workspaces --if-present && npm run lint --workspaces --if-present`

### Decisiones locales tomadas
- Next.js actualizó automáticamente `apps/web/tsconfig.json` durante el primer build (agrega allowJs, noEmit, incremental, module esnext, etc.) — comportamiento esperado del framework, no revertir.
- `.eslintrc.json` es necesario en apps/web para que `next lint` no entre en modo interactivo.
- `apps/api` no tiene `package.json` (es Python); npm workspaces lo lista pero no lo instala — funciona correctamente.
- `.env.example` no fue creado: archivos `.env*` bloqueados por permisos del entorno de CI. Crear manualmente con el contenido del PLAN.md Sección 9.

### Problemas conocidos
- `.env.example` pendiente de creación manual. No afecta la compilación ni el CI, pero es necesario para onboarding de nuevos devs.
- PR #1 en GitHub — CI corre lint + build en este PR.

### Tarea siguiente
- ID y nombre: T2 — Schema SQL inicial y migraciones Alembic
- Depende de: T1 ✓
- Primer paso concreto: crear `apps/api/alembic/versions/001_initial_schema.py` con todas las tablas, ENUMs e índices de PLAN.md Sección 2
- Archivos a leer primero: `docs/PLAN.md` Sección 2 (esquema completo) y Sección 4 T2 (criterio de done)
