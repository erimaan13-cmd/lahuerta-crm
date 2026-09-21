# Informe — Iteración 2 (sin depender del cliente)

Fecha: lunes 21-sep-2026, ≈03:30 h Monterrey. MODO ENSAYO: todo con datos sintéticos y sin tocar sistemas externos.

**Conclusión:** la medición honesta mostró que el clasificador del MVP era más débil de lo reportado: 53 % de exactitud con correos independientes, no 89 %. Con las nuevas reglas llega a **75 %**, y entre lo que clasifica solo acierta **87 %**. Además quedaron terminadas y probadas cinco funciones P1 y el endurecimiento de seguridad. Suben de 95 a **127 pruebas**, todas aprobadas.

## 1. Clasificador: medición honesta

- Se construyeron tres corpus sintéticos: 96 para ajuste, 66 de prueba del autor y 72 de prueba independiente. Los redactaron subagentes sin acceso a las reglas y quedaron congelados con hash antes de cualquier ajuste.
- **rules-1.0 → 1.1.1** (corpus independiente): exactitud **52.8 % → 75.0 %**; exactitud entre auto-clasificados **70.3 % → 87.0 %**; cobertura automática **51 % → 64 %**.
- Por qué el corpus del autor da 98.5 %: sesgo de autor. La cifra citable es la independiente.
- Se encontró y corrigió un defecto: "S.A. de C.V." activaba la regla de currículum.
- Huecos que siguen: primer contacto de prospectos sin palabras clave (recall 33 %), pedidos coloquiales (50 %) y quejas coloquiales (50 %).
- Detalle: `05_EVALUACION_CLASIFICADOR.md`.

## 2. Funciones nuevas (funcionan y están probadas)

| Función | Qué hace | Evidencia de negocio |
|---|---|---|
| SLA en horas hábiles | Los vencimientos respetan L–V 8–17 (hora de Monterrey) y los feriados de ley. Ej.: un lead que entra el viernes a las 16:30 vence el lunes a las 11:30, no el sábado | E13, E14 |
| Fusión de duplicados | Un botón integra el duplicado en el original: completa datos, mueve llamadas, tareas, casos y correos; el duplicado queda descartado con referencia | E17 |
| Cotización: estados y PDF | Borrador → enviada → aceptada / rechazada / vencida. PDF descargable con marca "DEMO". "Enviada" solo registra el envío manual y crea la tarea de seguimiento | E10, E14 |
| Alerta de recompra | Detecta clientes que pasaron su intervalo habitual de compra y crea una tarea para Ventas, una sola vez | E11 |
| Hora local | La interfaz muestra la hora de Monterrey (antes UTC) | E13 |

## 3. Seguridad y mantenimiento

- **CSRF** (falsificación de solicitudes desde otro sitio): cada formulario lleva un token.
- La API solo acepta JSON; responde 415 en otro caso.
- Bloqueo de 15 minutos tras 5 intentos fallidos de login.
- **Migraciones versionadas con Alembic** (0001 esquema del MVP, 0002 iteración 2). Una prueba verifica que migraciones y modelos no se desfasen y que el retroceso funcione.

## 4. Qué sigue simulado o pendiente

- Simulados: ERP, QMS, Gmail y LLM (sin cambio).
- La revisión de recompra corre bajo demanda. PENDIENTE: programarla una vez al día cuando haya servidor.
- Feriados propios de La Huerta: PENDIENTE.
- Métricas del clasificador con correos reales: PENDIENTE. No hay acceso.

## 5. Próximo paso recomendado (sin cliente)

Ajustar el recall de LEAD_NUEVO, PEDIDO y CALIDAD con un **corpus independiente nuevo**: el actual ya se usó.
