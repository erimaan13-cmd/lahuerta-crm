# 12 · Auditoría independiente del manual de uso

26 de septiembre de 2026. Revisión hecha por una sesión que no participó en escribir el manual ni
el sistema, verificando cada afirmación funcional contra el código.

**Resultado:** la mitad operativa del manual es exacta. La mitad comercial tiene diez afirmaciones
falsas. Corregirlas antes de enseñárselo a nadie.

## A. Promesas que el sistema no cumple

### A1 · "Solo el nombre es obligatorio" (cap. 5, línea 126)
`app/services/crm.py:80-83` exige nombre **y** correo o teléfono. Reproducido.
**Corrección:** "Nombre y al menos un dato de contacto (correo o teléfono) son obligatorios."
Y marcar ambos campos con asterisco en `leads.html`.

### A2 · "Ocho etapas; saltárselas es normal" (cap. 7, líneas 183-198)
`app/services/pipeline.py:17-36`. Las etapas dependen del **tipo** de oportunidad, que el manual
nunca menciona:
- `estandar` y `recompra`: solo requerimiento → cotizacion → negociacion → ganada/perdida. Las
  etapas de fórmula y muestra son inalcanzables.
- `formula_personalizada`: las ocho, **en orden estricto**; no se puede saltar a Cotización.

**Corrección:** agregar el concepto de tipo de oportunidad con una tabla de tres columnas, y
sustituir "saltarse etapas es normal" por "cada tipo tiene su camino y el sistema no deja salirse".
El mismo error está en `docs/diagrams/08_proceso_venta.mmd`.

### A3 · "Quien entrega suele ser Almacén" (cap. 8, línea 221)
`app/permissions.py:41`: el rol `almacen` no tiene `sales:write`. Las rutas de confirmar, entregar,
cancelar y facturar lo exigen (`app/routers/sales.py:64,71,78,86`) y los botones no se dibujan.
**Corrección:** "Captura, confirma y registra la entrega Ventas o Administración; Almacén ve el
pedido y su descuento de inventario, pero no puede moverlo." Y decidir en el backlog si Almacén
debe tener `sales:write`.

### A4 · La ficha de la cuenta muestra sus pedidos (cap. 6, línea 169)
`app/models.py:78`: `Account.orders` apunta a `OrderReference`, el espejo del ERP simulado, no a
`SalesOrder`. `sales.for_account()` (`sales.py:233`) existe y no lo llama ninguna ruta.
**Corrección:** decir que los pedidos se consultan en Pedidos filtrando por cliente. En el backlog:
conectar `sales.for_account` a la vista 360.

### A5 · Describe el módulo de Casos y quién escribe en él (cap. 10)
No existe ruta HTML de alta. `crm.create_case` solo se invoca desde la API JSON, desde
`email_pipeline.py:217` al aplicar una sugerencia, y desde el seed.
**Corrección:** "un caso nace al aplicar la sugerencia de un correo clasificado; todavía no hay
pantalla para abrirlo a mano". Una reclamación por teléfono no se puede registrar.

### A6 · El rastreo de lote a clientes "hoy funciona" (cap. 10, línea 302) — EL MÁS GRAVE
Los datos existen (`StockMovement.ref_type`, `ref_id`) pero `inventario_movimientos.html` filtra
solo por producto y bodega, no por lote, y la columna de referencia imprime "pedido" sin folio ni
cliente.
**Corrección:** quitar "hoy funciona". Poner: "los movimientos de salida guardan a qué pedido salió
cada kilo; hoy hay que abrir los pedidos uno por uno para saber el cliente". En el backlog: filtro
por lote y folio del pedido en la columna de referencia.

### A7 · "Una tarea se asigna a una persona o a un área" (cap. 14)
El formulario ofrece solo `assignee_role` y solo cuatro roles. No se puede pedir nada a Almacén,
Abastecimiento, Mantenimiento ni RRHH.

### A8 · "El correo repetido marca duplicado" (cap. 5)
`crm.py:99-108`: un correo idéntico **no crea registro nuevo**, suma la actividad al existente. La
marca de duplicado se pone por mismo teléfono o mismo dominio (`crm.py:119-138`).

### A9 · La orden de compra "queda en borrador, editable" (cap. 12, línea 383)
No existe ruta ni formulario de edición.

### A10 · Historial de precios en la ficha del proveedor (cap. 12, línea 385)
`procurement.price_history` es por producto y se pinta en la ficha de la orden de compra.

## B. Restricciones que el código impone y el manual no advierte

- Calificar un prospecto exige nombre de empresa (`crm.py:160`).
- Una oportunidad no llega a Cotización ni a Ganada sin cotización capturada (`crm.py:293,297`);
  una cerrada ya no se mueve (`:287`); "perdida" exige motivo (`:295`).
- El folio de factura no se captura en un pedido borrador ni cancelado (`sales.py:211`). La fecha
  prometida es obligatoria (`sales.py:64`).
- Una orden de compra **recibida** no se puede cancelar en absoluto (`procurement.py:31`). El
  manual lo cuenta mal: el caso real es la orden recibida **a medias**, que sí se cancela y deja
  dentro los kilos ya recibidos.
- Contratos: un temporal exige fecha de término posterior al inicio; a un empleado dado de baja no
  se le registra contrato nuevo; un puesto necesita al menos una función; un puesto no se puede
  editar (`hr.update_job_profile` sin ruta).
- Un correo en Needs Review necesita **dos** clics: confirmar o corregir, y luego aplicar
  (`email_pipeline.py:183`).
- Silenciar un aviso lo puede hacer cualquiera, incluido solo lectura, y solo hay dos plazos: 30
  días o sin fecha.
- El sistema **sí** maneja sacos, cajas y tarimas (`inventory.py:27,46`), y el manual lo presenta
  como pregunta abierta.
- Documento por vencer: solo hay tres rutas de destino; todo lo demás avisa a Administración.
- Contraseña temporal de mínimo 10 caracteres; no se puede desactivar al último administrador.

## C. Imprecisiones menores

- El tablero no es idéntico para todos: las tarjetas de Personal y Caja chica están condicionadas.
- "Se registra cada acción": hay excepciones deliberadas (D-55).
- La cuenta pasa a Cliente activo también al **ganar** una oportunidad, no solo al entregar. Y
  "Cliente recurrente" aparece en la interfaz pero ningún código lo asigna.
- Un plan de mantenimiento tampoco se puede desactivar (la otra mitad de MAN-1).
- El bloque de subida de documentos solo existe en cinco pantallas.
- `email:review` lo tienen también Ventas y Calidad; `case:write` también Administración.

## D. Lo que sí resistió la revisión

Verificado línea por línea y correcto: inventario completo (existencia como suma, nunca negativa,
ajuste con motivo, nada se borra), pedidos (confirmar solo verifica, entregar todo o nada con
rollback, PEPS por caducidad, "entregado" terminal), abastecimiento (umbral, autorización
exclusiva, lote obligatorio, recepción parcial), avisos (los seis tipos con todos sus umbrales,
idempotencia, y el diagnóstico de RN-4), mantenimiento, caja chica, personal, historial, permisos
y horario hábil. La honestidad del cap. 7 sobre el precio cero es correcta y ejemplar.

## E. Observación no dicha en el manual

Quien tiene el botón "Revisar ahora" (Administración) **no ve la mayoría de los avisos que
genera**: `notifications._visible` filtra por rol destino y los de lote, existencia y mantenimiento
van a `almacen` y `mantenimiento`. Quien haga la rutina diaria pulsa un botón cuyo efecto no puede
comprobar en su propia pantalla.
