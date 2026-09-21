# Informe — Iteración 3: historial total para administradores

Fecha: 21-sep-2026. MODO ENSAYO, datos sintéticos.

**Conclusión:** toda acción de todo usuario queda registrada. Solo los administradores la ven. Si alguien la altera directamente en la base de datos, el sistema lo detecta. **139 pruebas aprobadas.**

## Qué se registra

| Tipo | Ejemplos | Qué se guarda |
|---|---|---|
| Cambios de datos | crear lead, calificar, convertir, mover etapa, cotizar, fusionar, abrir caso, clasificar correo | Antes → después de cada campo |
| Consultas y envíos | abrir un lead, ver la lista de cuentas, descargar un PDF, exportar | Pantalla o ruta, resultado y duración |
| Seguridad | inicio y cierre de sesión, contraseña incorrecta, bloqueo, acceso sin permiso, cambios de usuarios | Motivo y resultado; nunca la contraseña |

Cada registro incluye fecha y hora de Monterrey, usuario, área (rol) al momento del evento, IP y número de solicitud.

## Dónde se ve (solo administradores)

- **Historial:** todo, con filtros por usuario, área, tipo, entidad, acción y fechas. Se exporta a CSV (abre en Excel).
- **Dentro de cada registro** (lead, cuenta, oportunidad, caso, correo): su historial propio.
- **Usuarios:** alta, desactivación, cambio de área y restablecimiento de contraseña, con acceso directo al historial de cada persona. Puede haber varios administradores; el sistema no permite quedarse sin ninguno.

## Protección del historial

- El sistema no tiene ninguna función para editar o borrar eventos.
- Cada evento guarda una huella (hash) del anterior. Si alguien edita o borra una fila directamente en la base, la página muestra **"Alerta de integridad"** e indica el evento afectado.

## Pendiente

Política de retención del historial de accesos, verificación por lotes cuando haya millones de eventos, y numeración segura con varios servidores (al pasar a PostgreSQL). Ver `BACKLOG.md` AUD-1 a AUD-4.
