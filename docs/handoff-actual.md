## HANDOFF — 2026-04-30 — Setup inicial del repositorio

### Tarea completada
- ID y nombre: Setup inicial — CLAUDE.md y docs de contexto
- Archivos creados/modificados:
  - `CLAUDE.md` → guía completa para Claude Code: commands, arquitectura, reglas de negocio, design tokens, testing, deploy, git workflow, handoff y criterios de escalada
  - `docs/handoff-actual.md` → este archivo
- Criterio de done verificado: sí — CLAUDE.md cubre todo lo necesario para que una nueva sesión arranque productiva
- Comando de verificación ejecutado: lectura directa del archivo generado ✓

### Decisiones locales tomadas
- Se adaptó el workflow de handoff/git al contexto de AlCosto: zonas prohibidas son los triggers de inmutabilidad, las reglas de negocio RN-XX y el schema de DB sin migración Alembic.
- Se mantuvieron los nombres de tareas en español (igual que el PLAN.md) para consistencia.

### Problemas conocidos
- Ninguno. El repositorio no tiene código aún; solo docs.

### Tarea siguiente
- ID y nombre: T1 — Setup del monorepo npm workspaces
- Depende de: ninguna ✓
- Primer paso concreto: crear `package.json` raíz con `workspaces: ["apps/web", "apps/api", "packages/shared"]`, luego scaffoldear cada workspace con su `package.json` mínimo.
- Archivos a leer primero: `docs/PLAN.md` Sección 4 (T1 — criterio de done) y Sección 1 (estructura de carpetas).
