# AlCosto — Plataforma Mayorista B2B

Plataforma web para importadores mayoristas. Permite a clientes B2B explorar un catálogo y realizar pedidos online, y al equipo interno gestionar catálogo y pedidos sin depender de WordPress.

## Stack

| Capa | Tecnología |
|------|------------|
| Frontend | Next.js 14 (App Router) + Tailwind CSS |
| Backend | FastAPI (Python) + SQLAlchemy 2.0 async |
| Base de datos | PostgreSQL (Railway) |
| Tipos compartidos | TypeScript (`packages/shared`) |
| Imágenes | Cloudflare R2 |
| Deploy | Vercel (frontend) + Railway (backend) |

## Estructura del monorepo

```
alcosto/
├── apps/web/          → Catálogo público + panel admin
├── apps/api/          → API REST (FastAPI)
└── packages/shared/   → Tipos TypeScript compartidos
```

## Setup local

**Requisitos:** Node 20+, Python 3.11+, Docker

```bash
# Clonar e instalar dependencias
git clone <repo>
cd alcosto
npm install

# Variables de entorno
cp apps/api/.env.example apps/api/.env
cp apps/web/.env.example apps/web/.env
# Completar los valores en cada .env

# Base de datos local
docker compose up -d

# Aplicar migraciones
cd apps/api
alembic upgrade head

# Levantar servicios
npm run dev --workspace=apps/web    # localhost:3000
uvicorn app.main:app --reload       # localhost:8000 (desde apps/api/)
```

## Scripts principales

```bash
npm run build --workspaces          # compilar todo
npm run lint --workspaces           # lint en todos los workspaces
pytest                              # tests backend (desde apps/api/)
pytest tests/test_rn_critical.py   # solo tests críticos
npx playwright test                 # E2E (desde apps/web/)
```

## Documentación

- [`docs/SPEC.md`](docs/SPEC.md) — Especificación funcional (el QUÉ)
- [`docs/PLAN.md`](docs/PLAN.md) — Arquitectura técnica y plan de implementación (el CÓMO)
- [`docs/handoff-actual.md`](docs/handoff-actual.md) — Estado de la sesión más reciente
- [`CLAUDE.md`](CLAUDE.md) — Guía para Claude Code
