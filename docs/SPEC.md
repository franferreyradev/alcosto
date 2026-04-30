# SPEC.md — AlCosto: Plataforma Mayorista B2B
**Versión:** 2.0 — Refactorizado bajo SDD  
**Fecha:** Abril 2025  
**Rol de este documento:** Define el QUÉ. No prescribe el CÓMO.  
**Artefacto siguiente:** PLAN.md (arquitectura técnica y stack)

---

## Propósito del sistema

AlCosto es una plataforma web para importadores mayoristas que permite a clientes B2B explorar un catálogo de productos y realizar pedidos online, y al equipo interno gestionar ese catálogo y los pedidos recibidos sin depender de WordPress.

El sistema debe crecer en fases. El MVP cubre catálogo y pedidos. El módulo de métricas y reportes es una segunda fase comercial que se habilita sin refactorizar infraestructura.

---

## Usuarios del sistema

| Usuario | Descripción |
|---|---|
| **Cliente mayorista** | Navega el catálogo, arma un carrito y confirma pedidos. No requiere cuenta. |
| **Operador (staff)** | Carga y edita productos desde el panel interno. Visualiza pedidos. |
| **Administrador** | Igual que staff + puede gestionar usuarios del panel. |

---

## Resultados esperados (outcomes)

### Para el cliente mayorista
- Puede explorar el catálogo completo de productos con imagen, nombre, código, descripción y precio unitario.
- Puede filtrar productos por nombre y categoría.
- Puede armar un carrito y confirmar un pedido cuando el total supera el mínimo de compra.
- Recibe confirmación del pedido con número de referencia.

### Para el operador / administrador
- Puede cargar un producto nuevo con su código externo, sin que el sistema asigne uno automáticamente.
- Puede editar cualquier campo de un producto existente.
- Puede activar o desactivar un producto del catálogo sin eliminarlo.
- Puede ver todos los pedidos recibidos y cambiar su estado.
- No necesita conocimientos técnicos para operar el panel.

---

## Reglas de negocio

Estas reglas son invariantes. Ninguna decisión técnica puede contradirlas.

### Productos
- `RN-01` El código de producto es numérico, lo asigna el operador manualmente y debe ser único. El sistema lo rechaza si ya existe.
- `RN-02` Un producto eliminado del catálogo nunca se borra de la base de datos. Solo se desactiva. Los pedidos históricos deben seguir siendo legibles.
- `RN-03` Cada producto tiene: código, nombre, descripción (campo libre), precio unitario, stock, categoría, imagen y estado activo/inactivo.
- `RN-04` El código de producto se muestra siempre como badge con la leyenda `COD:` seguida del número. Es visible en el catálogo y en el detalle del producto.

### Carrito y pedidos
- `RN-05` El monto mínimo de pedido es **$60.000**. El cliente no puede confirmar un pedido por debajo de ese monto.
- `RN-06` Mientras el carrito no alcance $60.000, el sistema muestra el progreso hacia ese mínimo pero bloquea la acción de confirmación.
- `RN-07` El precio de cada ítem se registra al momento de la venta y no puede modificarse retroactivamente. Si el producto cambia de precio después, los pedidos anteriores conservan el precio original.
- `RN-08` Un pedido puede tener los estados: pendiente, confirmado, despachado, cancelado. Solo el operador puede cambiar el estado.

### Identidad visual
- `RN-09` La paleta de colores es la del logo oficial de AlCosto: azul `#1B3FA0`, rojo `#C8181E`, amarillo `#F5C400`, gris `#8A8A8A`, fondo blanco `#F8F8F8`.
- `RN-10` El diseño transmite identidad de importador mayorista serio. No e-commerce genérico ni marketplace de consumo masivo.
- `RN-11` El badge `COD:` usa fondo amarillo (`#F5C400`) con texto azul oscuro (`#1B3FA0`).

### Migración inicial
- `RN-12` Los productos existentes en WordPress deben migrarse sin intervención manual del operador.
- `RN-13` Las imágenes existentes en WordPress se conservan mediante su URL original. No se requiere re-subir ninguna imagen en el lanzamiento.

---

## No-objetivos (MVP)

Lo siguiente está explícitamente fuera del alcance del MVP. El agente no debe implementarlo ni sugerirlo.

- Sistema de login para clientes mayoristas.
- Gestión de listas de precios diferenciadas por cliente.
- Integración de pagos online (MercadoPago, Stripe u otros).
- Notificaciones por email o WhatsApp al confirmar pedidos.
- Importación masiva de productos por CSV o Excel.
- Dashboard de métricas y reportes *(segunda fase comercial)*.
- Multi-idioma o multi-moneda.
- Sistema de descuentos o cupones.
- Gestión de proveedores.

---

## Criterios de aceptación por módulo

El sistema cumple la spec cuando todos estos criterios son verificables por tests automatizados o inspección manual.

### Catálogo público
- [ ] Un visitante sin cuenta puede ver todos los productos activos.
- [ ] Un producto inactivo no aparece en el catálogo ni es accesible por URL directa.
- [ ] Cada producto muestra: badge COD, nombre, descripción truncada, precio unitario, imagen.
- [ ] El filtro por nombre devuelve solo productos cuyo nombre contiene el texto ingresado.
- [ ] El filtro por categoría devuelve solo productos de esa categoría.
- [ ] El catálogo carga los primeros productos desde el servidor (relevante para SEO).
- [ ] El botón "Ver más" carga la siguiente página sin recargar la página completa.

### Carrito
- [ ] El cliente puede agregar y quitar productos del carrito.
- [ ] El carrito persiste si el cliente recarga la página.
- [ ] Mientras el total sea menor a $60.000, el botón de confirmación no está disponible.
- [ ] El sistema muestra el monto faltante para alcanzar el mínimo.
- [ ] Al superar $60.000, el botón de confirmación se habilita.
- [ ] El cliente puede completar nombre, teléfono, dirección y notas antes de confirmar.
- [ ] Al confirmar, el sistema registra el pedido con el precio de cada ítem al momento de la compra.
- [ ] El cliente recibe un número de pedido como confirmación.

### Panel de administración
- [ ] Solo usuarios con rol `admin` o `staff` pueden acceder al panel.
- [ ] Un acceso sin credenciales válidas redirige al login.
- [ ] El operador puede crear un producto ingresando su código numérico manualmente.
- [ ] El sistema rechaza un código que ya existe y muestra el error antes de intentar guardar.
- [ ] El operador puede editar cualquier campo de un producto existente.
- [ ] El operador puede desactivar un producto sin eliminarlo.
- [ ] El operador puede ver todos los pedidos con estado, cliente, monto y fecha.
- [ ] El operador puede cambiar el estado de un pedido.
- [ ] El operador puede ver el detalle completo de un pedido con los precios al momento de la venta.

### Migración desde WordPress
- [ ] El script de migración corre sin intervención manual.
- [ ] Todos los productos de WordPress quedan disponibles en el catálogo tras la migración.
- [ ] Las imágenes se muestran correctamente desde sus URLs originales de WordPress.
- [ ] El script imprime un reporte: productos migrados, errores encontrados.

### Módulo de reportes (fase 2)
- [ ] Desde el primer pedido confirmado, el sistema acumula datos suficientes para reportes de ventas por período, productos más vendidos, ticket promedio y clientes frecuentes.
- [ ] La activación del módulo no requiere migraciones de base de datos ni cambios de infraestructura.
- [ ] En el MVP, cualquier intento de acceso a endpoints de analytics devuelve un error de acceso denegado.

---

## Restricciones conocidas

- El código de producto viene de un sistema externo al que AlCosto no tiene acceso directo. El operador lo ingresa manualmente.
- WordPress seguirá activo sin fecha de cierre definida. La migración de imágenes a almacenamiento propio puede hacerse de forma gradual.
- El operador no tiene perfil técnico. Cualquier acción en el panel debe ser comprensible sin documentación adicional.

---

*Este documento es el contrato funcional del proyecto. Cualquier cambio de comportamiento del sistema debe comenzar con una actualización de esta spec. El PLAN.md derivado de este documento define el stack, la arquitectura técnica y el esquema de datos.*