# Backlog posterior al MVP

## Validaciones con La Huerta (bloquean decisiones, antes de programar P1)

1. ¿Qué proveedor de correo usan (Google Workspace, Microsoft 365, otro)? → define RF-30.
2. ¿Tienen ERP / sistema contable? ¿Cuál? → define RF-39.
3. ¿Quién atiende hoy formularios, WhatsApp y `administracion@`? → roles reales y enrutamiento.
4. Lista real de productos, sectores y opciones de los formularios (E22).
5. Política de precios, aprobaciones y crédito.
6. Entrega propia o tercerizada; zonas de cobertura.
7. Volumen diario de correos y de leads (dimensiona la necesidad de LLM y colas).
8. Tratamiento de datos personales para usar un LLM externo (aviso de privacidad, E16).
9. ¿Quién aprueba las compras: el dueño, o hace falta un rol de jefe de compras que autorice sin poder crear órdenes? → define si se agrega un rol (ver OPE-3 y D-58).
10. ¿Existen de verdad las diez áreas del organigrama, o una sola persona cubre varias? → define si sobran roles.
11. ¿Quién trabajará en computadora y quién en celular? → define qué pantallas conviene optimizar.
12. **Cuando confirman un pedido, ¿apartan el producto físicamente en la bodega, o se surte hasta el día de la salida? ¿Ha pasado que dos pedidos prometan el mismo producto y no alcance?** → define RN-1.
13. **Si un cliente les reporta un problema con un lote, ¿qué hacen hoy, paso por paso, desde que les llama hasta que recuperan el producto?** Y en particular: cuando un cliente regresa mercancía, o cuando el proveedor manda producto que no pasa calidad, ¿qué hacen con esos kilos — los vuelven a meter al almacén, los separan, los tiran? ¿Quién lo anota y dónde? → define **RN-5**, el riesgo de mayor peso comercial del sistema.
14. **¿Les pasa que surten un pedido a medias porque no alcanzó el producto? Si sí, ¿cómo lo registran hoy y cómo sabe el cliente qué le queda pendiente?** → define RN-3.

## P1 — siguiente iteración

| ID | Tarea | Por qué | Esfuerzo |
|---|---|---|---|
| RF-43 | Migrar a PostgreSQL gestionado (las migraciones Alembic ya existen) + despliegue con HTTPS | Usuarios reales, respaldos gestionados | M |
| RF-30 | Adaptador Gmail/Graph **solo lectura** (OAuth del cliente) | Ingesta real | M |
| RF-32 | Webhook del formulario web con token y anti-spam | Leads entran solos | S |
| RF-40b | Tablero de métricas del clasificador a partir de las correcciones en Needs Review (la evaluación offline ya existe) | Medir con datos reales | S |
| CLS-2 | Recall de LEAD_NUEVO / PEDIDO / CALIDAD coloquial; desempate PEDIDO > SEGUIMIENTO; spam tipo SAT — **con corpus independiente nuevo** | Hallazgos de `05_EVALUACION_CLASIFICADOR.md` | M |
| AUT-1 | Programador diario para `run_reorder_check` y tareas vencidas | Hoy es bajo demanda | S |
| RF-31 | Activar LLM en modo híbrido con presupuesto y registro de costo | Correos atípicos / inglés | M |
| RF-36b | Versionado de cotizaciones (v2, v3 de un mismo folio) | Negociación | S |
| RF-37 | Aprobación de precio especial | Negociación | S |
| RF-39 | Adaptador ERP real (clientes, pedidos, crédito) | Sustituir mock | M–L |
| RF-41 | Derechos ARCO: exportar/anonimizar contacto | Privacidad (E16) | S |
| RF-42 | Notificaciones internas (correo/Slack) de tareas vencidas | Seguimiento | S |
| NFR | Rotación de `CRM_SECRET_KEY`, cabeceras de seguridad (CSP, HSTS), límite de login en almacenamiento compartido | Antes de exponer a internet | S |
| NFR | Paginación en listas | Rendimiento con volumen real | S |
| AUD-1 | Política de retención del historial de accesos (p. ej. 12–24 meses) y archivo en frío | El historial crece ≈1 fila por clic | S |
| AUD-2 | Verificación de integridad por lotes/puntos de control (hoy recalcula toda la cadena al abrir la página) | Rendimiento con millones de eventos | S |
| AUD-3 | Secuencia de la BD o bloqueo para numerar la cadena con varios procesos (PostgreSQL) | Concurrencia en producción | S |
| AUD-4 | Rol "auditor" (ve historial sin editar datos) si La Huerta lo pide | Separación de funciones | S |

## P2 — congelado durante el MVP

Disponibilidad de inventario desde WMS · apertura de no conformidades en QMS con retorno de estado · portal de clientes · pronóstico de ventas · automatización de marketing · canal retail (visión E12) · modelo ML entrenado con etiquetas acumuladas · borradores de respuesta asistidos (siempre con aprobación humana) · permisos por registro/propietario · multi-idioma en el clasificador.

## Hecho en la iteración 2 (sin depender del cliente)

RF-34 SLA hábil · RF-35 fusión de duplicados · RF-36 PDF y estado de cotización · RF-38 alerta de recompra · evaluación independiente del clasificador (rules-1.0 → 1.1.1) · CSRF · límite de intentos de login · API solo JSON · migraciones con Alembic · hora local en la interfaz.

## Hecho en la iteración 4 — operación interna (23-sep-2026)

Inventario con lotes, bodegas y movimientos · abastecimiento con autorización y recepción · pedidos
que descuentan inventario · mantenimiento de activos con planes por días/km/horas · expedientes de
personal con contratos y alertas · caja chica con comprobante obligatorio · avisos silenciables ·
adjuntos con vencimiento · cuatro roles nuevos · tableros por módulo. Detalle en `06_OPERACION.md`.

## P1 de la operación interna (siguiente iteración)

| ID | Tarea | Por qué |
|---|---|---|
| FAC-1 | Pestaña de facturación por lectura del XML del CFDI | El cliente factura en CONTPAQi; el XML no necesita OCR ni licencias |
| FAC-2 | Conector con el SDK de CONTPAQi Comercial Premium (si esa es su versión) | Existencias y precios en vivo; requiere PC Windows encendida |
| OPE-1 | Tarea programada diaria que ejecute `notifications.generate` | Hoy los avisos se generan a demanda |
| OPE-2 | Adaptador de envío de correo para los avisos | Quedan en cola como `sin_adaptador` |
| OPE-3 | Preguntar a La Huerta: **¿quién aprueba las compras: el dueño, o hace falta un rol de jefe de compras que autorice sin poder crear órdenes?** Y confirmar el umbral de $20,000 MXN | Que hoy solo autorice `admin` es separación de funciones y **se queda así** (D-58): si Abastecimiento tuviera la llave aprobaría sus propias compras. La pregunta es si se necesita un rol intermedio |
| OPE-4 | Recepciones con varios lotes por renglón (tabla de recepciones) | Hoy el renglón guarda el último lote; el rastro completo está en los movimientos |
| OPE-5 | Campos de baja en el expediente (fecha y motivo) para reporte de rotación | Hoy van en notas y bitácora |
| OPE-6 | Aviso de privacidad para empleados y política de uso del sistema | Obligatorio antes de cargar expedientes reales |
| OPE-7 | Migrar lo que hoy llevan en Excel | PENDIENTE de saber qué existe |

## Interfaz — hallazgos del recorrido por rol (25-sep-2026)

Los tres salen de `09_RECORRIDO_POR_ROL.md`. **Ninguno está implementado**; se anotan para decidirlos
después. Los tres conservan la visibilidad cruzada del menú, que se queda como está por decisión
(D-57).

| ID | Tarea | Por qué | Esfuerzo |
|---|---|---|---|
| UI-1 | El mensaje de bloqueo debe decir de quién es la sección y a quién pedírsela, no el código del permiso | Hoy se lee "Tu rol no tiene el permiso 'pettycash:read'"; un almacenista no sabe qué significa | S |
| UI-2 | Reordenar el menú para que el bloque del área de cada quien quede primero, conservando el resto visible | Alguien de almacén ve cinco secciones comerciales antes de llegar a Inventario (ley de Hick) | S |
| UI-3 | Tablero adaptado al rol | Hoy es el mismo para todos y es la pantalla más densa (22 renglones): útil para ventas, ruido para un mecánico | M |
| UI-4 | Decidir si silenciar un aviso debe seguir al alcance de todos los roles | **VERIFICADO con prueba:** silenciar y marcar leído exigen solo `notification:read` (`app/routers/notifications.py:31` y `:39`), que tienen los diez roles, así que el rol `lectura` puede apagar una alerta de lote por caducar (se comprobó entrando como `direccion@demo.local`). El código lo hace a propósito ("silenciar es decisión del área"), pero un usuario de consulta no debería poder | S |

## Mantenimiento — funciones sin puerta de entrada (25-sep-2026)

Los tres salieron de la revisión de la Fase 2. VERIFICADOS leyendo el código.

| ID | Tarea | Por qué | Esfuerzo |
|---|---|---|---|
| MAN-1 | Exponer `cancel_work_order` y `set_plan_active` por HTTP | Ambas funciones existen en `app/services/maintenance.py` (`:275` y `:191`), validan bien y auditan, pero **ninguna ruta las invoca**: desde la interfaz no se puede cancelar una orden de trabajo ni desactivar un plan | S |
| MAN-2 | Implementar la transición a `en_proceso`, o quitar el estado | El estado está declarado en el servicio y en el modelo (`models.py:608`) pero **ninguna función lo asigna**: es inalcanzable. Una orden solo puede estar abierta, cerrada o cancelada | S |
| MAN-3 | Decidir si las refacciones salen del inventario y si el costo se desglosa | Hoy mantenimiento **no descuenta piezas** (solo usa un ayudante numérico del módulo de inventario) y el costo es un total sin separar mano de obra. PENDIENTE de saber si La Huerta lleva refacciones en inventario | M |

## RIESGOS DE NEGOCIO — no son dudas del cliente, son huecos que van a costar dinero (25-sep-2026)

Subidos de categoría por decisión de Erick el 25-sep-2026: los tres estaban anotados como preguntas al
cliente y se reclasifican porque **el daño ocurre aunque el cliente no responda nada**. VERIFICADOS
leyendo el código y, en el caso de RN-1, reproducidos. **Ninguno está implementado.**

| ID | Riesgo | Por qué es un riesgo, no una duda | Esfuerzo |
|---|---|---|---|
| RN-1 | **Confirmar un pedido no aparta existencia.** Dos vendedores pueden comprometer los mismos kilos y el conflicto no aparece hasta el momento de entregar | `confirm()` (`app/services/sales.py:146`) solo *consulta* la existencia con `check_stock`, que es lectura pura: no crea movimiento, no marca nada y no hay tabla ni columna de reserva. `deliver()` vuelve a revisar y ahí sí falla. Consecuencia comercial: dos clientes reciben promesa de entrega sobre el mismo lote, y quien pierde se enterará el día que esperaba su mercancía. Con un solo vendedor el riesgo es bajo; con dos o más es cuestión de tiempo. Hoy hay **dos usuarios de ventas** en el sistema | M |
| RN-3 | **Asimetría entre compras y ventas**: se puede recibir una orden de compra a medias, pero no entregar un pedido a medias | En compras, un renglón en cero se ignora y la orden sigue abierta para recibir el resto (`procurement.py:248`). En ventas, `deliver()` surte todos los renglones o ninguno y deshace la operación completa si uno falla (`sales.py:164-185`). El sistema modela la realidad del proveedor pero no la del cliente, y la entrega parcial es más común hacia el cliente que desde el proveedor. **Hay que decidir en qué sentido se empareja**: permitir entrega parcial en ventas, o exigir recepción completa en compras. Dejarlo asimétrico obliga a la gente a inventarse un truco (capturar dos pedidos, o entregar de menos y ajustar), y esos trucos son los que ensucian el historial | M |

| **RN-5** | **No se puede hacer un retiro de producto.** Tiene su propia sección enseguida, porque son cuatro piezas | **Es el riesgo de mayor peso comercial del sistema** y absorbe lo que antes era RN-2. Ver la sección siguiente | M–L |
| RN-4 | **El sistema de avisos solo corre si alguien pulsa "Revisar ahora"**, botón que solo tienen dos roles. Sin tarea programada y sin correo, **un aviso de caducidad no existe hasta que alguien se acuerda de pedirlo** | Tres hechos VERIFICADOS que se suman: (1) `notifications.generate` no tiene programador — ningún código lo llama solo, solo la ruta `POST /avisos/generar` (`app/routers/notifications.py:57`); (2) esa ruta exige `integration:run`, que solo tienen `admin` y `administracion`, así que ni Almacén ni Mantenimiento ni RRHH pueden generar los avisos que van dirigidos a ellos; (3) el envío de correo está apagado y **no existe ningún código que envíe correo** en el proyecto, así que todo aviso nace con estado `sin_adaptador` y solo se ve entrando al sistema. Consecuencia: el lote que caduca en 30 días, el contrato que vence en 60 y la existencia bajo el mínimo **no avisan a nadie** si nadie pulsó el botón. El sistema parece vigilar y no vigila. Es el segundo riesgo más grave después de SEC-1. Las piezas ya estaban anotadas por separado como OPE-1 y OPE-2; aquí se juntan porque el riesgo es la combinación, no cada una | M |

**Las preguntas de negocio que se derivan de RN-1 y RN-3** están al inicio de este documento,
en la lista de validaciones con La Huerta (puntos 12 y 14), redactadas para preguntárselas a una
persona, no a un programador. RN-4 no necesita pregunta: hay que arreglarlo. **RN-2 dejó de existir por
su cuenta: se absorbió en RN-5**, más abajo.

## RN-5 · NO SE PUEDE HACER UN RETIRO DE PRODUCTO (26-sep-2026)

**El riesgo de mayor peso comercial de todo el sistema.** Agrupado por decisión de Erick el 26-sep-2026:
los cuatro hallazgos estaban sueltos y por separado parecían detalles técnicos. Juntos dicen una cosa
sola, y es grave:

> **Si un cliente reporta un problema con un lote, el sistema no permite frenarlo, no permite recibirlo
> de vuelta, y no permite saber con certeza a quién más se le vendió.**

Para una empacadora de alimentos con certificación FSSC 22000, eso es exactamente lo que un retiro de
producto —un *recall*— exige poder hacer. Los cuatro son VERIFICADOS en el código, y dos reproducidos
con pruebas.

| Pieza | Qué falta | Qué impide hacer |
|---|---|---|
| **a) No se puede bloquear un lote** | No existe ninguna función para marcar un lote como retenido o sospechoso. `inventory.move()` no consulta ningún estado del lote | **Frenar la salida.** Mientras se investiga la queja, el lote sigue disponible y cualquiera puede surtirlo en el siguiente pedido |
| **b) No se impide vender un lote caducado** | `move()` no compara `lot.expires_on` con la fecha de hoy. Las caducidades solo alimentan avisos, que son informativos | **Confiar en el sistema como barrera.** Hoy la única barrera es que alguien lea el aviso — y los avisos no se generan solos (RN-4) |
| **c) No se puede registrar una devolución ni producto rechazado** (antes RN-2) | No hay función de devolución en ventas ni en compras. `cancel()` no revierte inventario, y `entregado` es estado terminal. La única salida es un ajuste manual, que no distingue una devolución de un error de captura ni guarda de qué cliente vino | **Recibir el producto de vuelta.** En cuanto entra el primer kilo devuelto, la existencia del sistema deja de coincidir con la bodega y nadie sabrá por qué |
| **d) Las salidas sin lote rompen el rastro** (antes INV-1) | Una salida manual sin lote se valida contra el total de la bodega y se guarda con `lot_id = NULL`. **Reproducido:** entrada de 100 kg al lote L1 y salida de 50 kg sin lote dejan la pantalla con dos renglones, −50 kg "sin lote" y 100 kg en L1. El total (50 kg) es correcto; el lote miente | **Saber a quién se le vendió.** La entrega de pedidos sí reparte por caducidad y queda bien; la captura manual es la que abre el hueco |

### Lo que sí funciona hoy, y por qué vale la pena arreglar el resto

El rastreo **existe y es bueno**: la recepción exige código de lote obligatorio, la entrega de un pedido
reparte por caducidad y deja movimientos con referencia al pedido, y Calidad puede ver por esos
movimientos a qué clientes salió un lote. La base está puesta. Lo que falta son las cuatro piezas de
arriba, y ninguna es un rediseño.

### Orden sugerido

1. **(d)** Exigir lote en toda salida, o repartir la salida sin lote por PEPS. Es la más pequeña y sin
   ella las otras tres descansan sobre datos inciertos.
2. **(a)** Estado del lote (disponible / retenido) consultado por `inventory.move()`.
3. **(c)** Devolución de cliente y rechazo a proveedor como movimientos con su propia referencia.
4. **(b)** Bloquear la salida de lote caducado, con excepción autorizada y registrada.

**La pregunta al cliente** está en la lista de validaciones, punto 13, y es la que debe hacerse primero:
*"si un cliente les reporta un problema con un lote, ¿qué hacen hoy, paso por paso, desde que les llama
hasta que recuperan el producto?"*. La respuesta dirá si el sistema debe reproducir su procedimiento
actual o ayudarles a construirlo.

## SEGURIDAD — los adjuntos y el permiso de su módulo (25-sep-2026)

**Los dos quedaron resueltos el 26-sep-2026**, SEC-1 con la decisión D-59 y SEC-2 con la D-61. En total
32 pruebas fijan el comportamiento en `tests/test_documentos_permisos.py`.

| ID | Tarea | Por qué | Esfuerzo |
|---|---|---|---|
| ~~SEC-2~~ **RESUELTO el 26-sep-2026** (D-61) | La **subida** de adjuntos pedía solo `attachment:write`, sin mirar a qué entidad apuntan | `POST /documentos` exigía `attachment:write`, que tienen nueve de los diez roles, y **no comprobaba el `entity_type`**: alguien de Almacén podía plantar un archivo en el expediente de un empleado. Es un problema de **integridad**: quien lo viera en RRHH supondría que lo puso RRHH. Ahora exige el permiso de escritura del módulo dueño, con la misma tabla y el mismo fallo cerrado que D-59 | S |
| ~~SEC-1~~ **RESUELTO el 26-sep-2026** (D-59) | `GET /documentos/{id}` y `GET /api/documentos/{id}` deben exigir el permiso del módulo dueño del adjunto (`hr:read` para `employee`, `pettycash:read` para `petty_cash`, etc.), no `dashboard:read` | **VERIFICADO con una prueba reproducible.** Ambas rutas piden solo `dashboard:read` (`app/routers/files.py:31` y `:47`), que está en `BASE_READ` y por tanto lo tienen **los diez roles**, y no comprueban a qué entidad pertenece el archivo. Comprobado entrando como `direccion@demo.local` (rol `lectura`): recibe **403 en `/caja`** y aun así **descarga con 200 el comprobante de caja chica** y lee su contenido, lo mismo por la API. Con expedientes reales esto expondría identificaciones y contratos de empleados a cualquier usuario autenticado. Contradice la regla 4c de CLAUDE.md y la decisión D-40. Agrava el riesgo que `GET /documentos` (`files.py:39`, mismo permiso) liste documentos de todas las entidades con sus identificadores | S |

**Efecto lateral aceptado de D-61:** Atención a clientes ya no puede adjuntar documentos a una **cuenta**,
porque no tiene `account:write`. Sí puede adjuntarlos a los **casos**, que es su trabajo. Si en la
práctica necesita ambos, la salida es darle `account:write`, no relajar la regla.

## Deuda técnica conocida

- Folios COT/CASO por conteo: posible colisión con concurrencia alta → secuencia en PostgreSQL.
- Reglas del clasificador en español con cobertura básica de inglés; todos los corpus son sintéticos.
- Límite de login en memoria de proceso (no sirve con varios procesos/servidores).
- Feriados propios de La Huerta no configurados (`EXTRA_HOLIDAYS`).
- Los corpus de evaluación ya fueron vistos; el próximo ajuste requiere un corpus independiente nuevo.
- Sesión por cookie firmada sin revocación del lado servidor.
- `IntegrationEvent` de salida no tiene worker que los despache (outbox listo, consumidor pendiente).
- Los archivos adjuntos viven en disco local (`data/uploads`): en la nube hay que montarlos en
  almacenamiento persistente o pasarlos a un bucket antes de exponer el sistema.
- Folios PED/OC/OM por conteo: misma limitación de concurrencia que COT/CASO (secuencia en PostgreSQL).
- Las métricas del tablero recorren las tablas completas; con años de operación conviene agregarlas.
