# 10 · Los diagramas explicados en palabras

Septiembre 2026. Acompaña a los diagramas de `docs/diagrams/`. Cada sección explica un diagrama para
alguien que no sabe leer diagramas: qué mira, en qué orden y qué debe concluir.

Etiquetas de evidencia: **VERIFICADO** = comprobado en el código o corriendo el sistema ·
**INFERIDO** = razonamiento que puede estar equivocado · **PENDIENTE** = falta preguntárselo al cliente.

## Cómo leer los tres colores de los diagramas de proceso

Cada paso de un proceso es una de tres cosas, y distinguirlas es el punto del ejercicio:

| Tipo | Cómo se ve | Qué significa |
|---|---|---|
| **SISTEMA** | Caja azul, esquinas rectas | Hoy lo hace el sistema. Está programado y se puede demostrar. |
| **FUERA** | Caja gris de borde punteado, esquinas redondeadas | Seguirá pasando fuera del sistema: CONTPAQi, el teléfono, WhatsApp, el papel, el camión. |
| **INCÓGNITA** | Caja amarilla de seis lados | **No sabemos cómo se hace hoy en La Huerta.** Es la lista de lo que hay que ir a preguntar. |

Cada etiqueta va además escrita con palabras dentro de la caja (`SISTEMA -`, `FUERA -`,
`INCOGNITA -`). Es a propósito: si Lucidchart pierde los colores al importar, el significado sigue
ahí. INFERIDO: conviene revisarlo tras la primera importación.

---

## 1. `04_arquitectura_logica.mmd` — cómo está construido el sistema

**Qué estás viendo.** El plano del edificio, no del trabajo. Se lee de arriba hacia abajo y las
flechas van en un solo sentido, lo cual es la idea central: cada capa solo habla con la de abajo.

- **Capa 1, rutas.** Reciben el clic del navegador. Su único trabajo es revisar que quien pide tenga
  permiso y que los datos vengan bien formados. **No deciden nada del negocio.** El CRM comercial vive
  en `main.py`; los siete módulos de operación tienen cada uno su propio archivo en `routers/`.
- **Capa 2, servicios.** Aquí viven las reglas: qué se puede y qué no. Cada módulo tiene su servicio.
- **Capa 3, modelos.** La forma de las tablas y sus restricciones, y debajo la base de datos.
- **Transversal.** Piezas que usan todas las capas: sesión y plantillas, la matriz de permisos, la
  bitácora, la hora hábil de Monterrey y la configuración.

**Las cuatro reglas que el diagrama hace evidentes**, todas VERIFICADAS leyendo el código:

1. **Ninguna ruta edita ni borra la bitácora.** Las flechas hacia `audit_events` solo entran. Además
   de cada cambio de datos, se registra **cada solicitud, incluso las denegadas**. La única excepción
   documentada es el contador de avisos que el navegador consulta en cada carga de página (D-55).
2. **Solo `inventory.move()` escribe movimientos de inventario.** Lo comprobé buscando quién llama a
   esa función en todo el proyecto: únicamente pedidos (una salida) y compras (una entrada). Ningún
   módulo mete la mano en las tablas de otro.
3. **La existencia es la suma de los movimientos.** No hay ninguna columna de saldo en ningún lugar:
   ni el producto, ni el lote, ni la bodega la tienen. Cada consulta vuelve a sumar. Es más lento y
   es a propósito: un saldo guardado se desincroniza y nadie sabe cuándo empezó a mentir.
4. **El sistema no emite facturas fiscales.** CONTPAQi aparece a propósito fuera de la caja del
   sistema. Del pedido sale una sola flecha hacia allá, y lo único que regresa es un folio que alguien
   captura a mano.

**Un dato que descubrí y conviene saber:** el módulo de mantenimiento **no descuenta refacciones del
inventario**. Importa del inventario únicamente un ayudante para leer números. VERIFICADO. Si una
reparación consume una pieza, hoy eso no baja de ninguna existencia. PENDIENTE: ¿La Huerta lleva
refacciones en inventario?

---

## 2. `08_proceso_venta.mmd` — del prospecto al pedido entregado

**El recorrido completo**, y lo que el sistema sí garantiza:

El cliente pregunta por algún canal (FUERA). Se da de alta un prospecto y **el sistema crea solo la
tarea de primer contacto, con vencimiento a 4 horas hábiles** contando horario de Monterrey. Alguien
llama (FUERA), registra la llamada y el prospecto pasa a *contactado*. Si el volumen llega a 500 kg
se califica y al **convertir** nacen de un golpe tres cosas: la cuenta, el contacto y la oportunidad.

La oportunidad recorre hasta ocho etapas, y **saltárselas es normal**: una recompra de catálogo va de
Requerimiento directo a Cotización. La cotización genera un PDF con folio, pero **el sistema no lo
envía**: alguien lo descarga y lo manda. Al marcarla como enviada, se crea la tarea de seguimiento.

Cuando se gana, se captura el pedido. Aquí hay tres cosas que quiero que sepas, todas VERIFICADAS:

- **Confirmar un pedido revisa la existencia pero no la aparta.** No hay reserva. Dos pedidos
  confirmados pueden comprometer los mismos kilos, y el segundo falla recién al momento de entregar.
- **Entregar es todo o nada.** Si un solo renglón no alcanza, no se descuenta ninguno: el sistema
  deshace la operación completa. No existe la entrega parcial.
- **Al entregar, sale primero el lote que caduca antes** (lo que en almacén se llama PEPS: primeras
  entradas, primeras salidas). El sistema lo decide solo, ordenando por fecha de caducidad.

Después, CONTPAQi factura (FUERA) y alguien captura el folio. La cuenta pasa sola de *Cliente
potencial* a *Cliente activo*, y más adelante la alerta de recompra propone una oportunidad nueva
calculando el intervalo promedio entre pedidos más 20 % de tolerancia.

**Las nueve incógnitas de este proceso.** Son lo más valioso del diagrama:

1. ¿Quién recibe cada canal y en cuánto tiempo responde?
2. ¿Quién autoriza un descuento o un precio especial? (VERIFICADO: hoy el sistema **no valida el
   precio**; un pedido puede quedar en $0 sin avisar.)
3. ¿Cómo llega la orden en firme del cliente: llamada, correo, orden de compra en papel?
4. ¿Hoy se aparta producto al confirmar un pedido?
5. ¿El reparto es propio o por paquetería, y se firma evidencia de entrega?
6. ¿Quién captura el folio de la factura y en qué momento?
7. ¿El sistema debería avisar de facturas por cobrar? (Hoy no registra cobranza.)
8. ¿Qué se hace con una devolución o con producto rechazado? Hoy **no existe en el sistema**: un
   pedido entregado es un estado final y no se revierte.
9. ¿Se entregan pedidos parciales? Hoy el sistema no lo permite.

---

## 3. `09_proceso_compra.mmd` — de la necesidad al lote en bodega

**El recorrido.** El sistema avisa cuando una existencia baja del mínimo del producto, pero **no crea
la orden solo**: alguien tiene que verlo y decidir. Se captura la orden en borrador con folio `OC-`,
sus renglones en kilos y el costo unitario.

Al enviarla ocurre la única bifurcación automática del proceso, VERIFICADA: **si el total pasa de
$20,000 MXN queda "por autorizar"; si no, queda autorizada sin que nadie firme.** Autorizar es
exclusivo del administrador (D-58).

Luego alguien le pide la mercancía al proveedor (FUERA) — **el sistema no manda la orden, ni por
correo ni en PDF** — y cuando llega se registra la recepción. Ahí el sistema es estricto en un punto
y flexible en otro:

- **Estricto:** el código de lote es obligatorio. Sin él no se puede recibir. Es lo que sostiene la
  trazabilidad que pide FSSC 22000.
- **Flexible:** la caducidad es opcional. Si no se captura y el producto tiene vida útil definida, el
  sistema la calcula sumando los días a la fecha de recepción.

La recepción **puede ser parcial**: los renglones que se dejan en cero se ignoran y la orden sigue
autorizada para recibir el resto. Solo cuando llegan todos los kilos pasa a "recibida". Cada
recepción crea el lote si no existía y mete una **entrada** al inventario por la única vía permitida.

**Las ocho incógnitas de este proceso:**

1. ¿Quién revisa el aviso de bajo mínimo y cada cuándo?
2. ¿Se compra por mínimos, por temporada, o cuando lo pide producción?
3. ¿Se piden varias cotizaciones antes de comprar? Hoy el sistema **no guarda cotizaciones de
   proveedor**: la orden es el primer documento que existe.
4. ¿El umbral de $20,000 MXN es el real?
5. ¿Hace falta un jefe de compras que autorice sin poder crear órdenes? (Ver D-58.)
6. ¿Cómo se le pide hoy al proveedor, y quién recibe en el andén y revisa calidad?
7. ¿Se rechaza un lote con poca vida útil, y cuál es el mínimo aceptable?
8. ¿Qué se hace con mercancía rechazada o devuelta? Hoy **no existe en el sistema**, y cancelar una
   orden ya recibida **no revierte el inventario**.

**Tres cosas que el módulo de compras no hace**, VERIFICADAS por ausencia en el código: no registra
pagos, plazos ni anticipos (no hay cuentas por pagar); no maneja IVA, descuentos, flete ni moneda
extranjera, aunque el proveedor pueda marcarse como "importado"; y no guarda datos fiscales del
proveedor.

---

## 4. `10_proceso_personal.mmd` — del puesto al expediente y sus contratos

**El recorrido.** Primero se describe el **puesto**: título único, área, y sus funciones y requisitos,
uno por renglón. Aquí conviene aclarar un malentendido: el documento 08 lo llamaba "puesto por
puntos", y **no hay ninguna puntuación ni valuación**. Son viñetas: una función por línea. VERIFICADO.

El reclutamiento entero ocurre fuera del sistema. Cuando alguien entra, se captura su expediente
(número de empleado, nombre, área, puesto, fecha de ingreso, teléfono y correo) y queda *activo*.
Después se registra el contrato, que puede ser temporal o indeterminado, con una regla firme: **un
solo contrato vigente por empleado**. El PDF firmado se sube y se guarda tal cual, sin leerlo.

**Lo que el sistema vigila solo:** si el contrato tiene fecha de fin, avisa **60 días antes** a RRHH,
y repite el aviso una vez por semana, no cada vez que alguien entra. Un contrato indeterminado no
vence y por tanto nunca avisa. Los documentos escaneados con vencimiento avisan a 30 días.

Al renovar, el contrato anterior queda marcado como *renovado* y nace uno nuevo; la cadena queda
completa. Al dar de baja a alguien, **nada se borra**: cambia a estado *baja*, exige motivo y cierra
los contratos vigentes.

**Lo que NO hace**, VERIFICADO por ausencia: **no calcula nómina** — no existe ninguna columna de
salario en el expediente —, no registra asistencia, vacaciones ni incidencias, no emite contratos en
PDF ni recibos, y no se conecta con IMSS ni SAT.

**Las incógnitas, y una obligación:**

1. **Falta el aviso de privacidad firmado antes de cargar expedientes reales.** No es una pregunta: es
   un requisito legal y ya estaba anotado como OPE-6.
2. ¿Existen descripciones de puesto escritas hoy, o hay que redactarlas?
3. ¿Hacen falta RFC, CURP, NSS, domicilio y salario? Hoy el expediente **no los guarda**.
4. ¿Se necesita reporte de rotación? Hoy la fecha y el motivo de baja se guardan como texto libre
   dentro de las notas, no en campos propios (ya anotado como OPE-5).
5. ¿Con qué sistema se calcula la nómina hoy?
6. ¿Se lleva asistencia o vacaciones en algún lado?

---

## 5. `11_proceso_caja_chica.mmd` — del gasto al reporte para el contador

**El recorrido.** Se da de alta un fondo con su monto y su responsable. Cada vez que alguien gasta
efectivo, se captura el gasto con monto, categoría y descripción, y aquí el sistema es inflexible a
propósito: **el comprobante es obligatorio**. Sin archivo adjunto no se registra el gasto. VERIFICADO.
Se aceptan PDF, foto, XML o texto de hasta 15 MB, y **no se lee el contenido**: el sistema lo guarda,
no lo interpreta.

**El saldo se calcula así:** monto del fondo + reposiciones − gastos, y se recalcula en cada consulta.
No hay columna de saldo guardado. Si un gasto no cabe en el saldo, el sistema lo rechaza con el
mensaje "registra primero una reposición": **el saldo nunca queda negativo**. VERIFICADO.

La reposición es simplemente un movimiento de signo contrario, capturado a mano, y ahí el comprobante
sí es opcional. Al final, un CSV con ocho columnas se le entrega al contador, que lo captura en su
sistema (FUERA).

**Dos cosas importantes que el sistema no hace**, VERIFICADAS: **no contabiliza** — no hay cuentas
contables, pólizas, centros de costo ni IVA; el CSV es la única salida — y **no tiene ningún flujo de
autorización** de gastos, a diferencia de compras, que sí exige firma sobre el umbral. Tampoco se
puede editar ni borrar un movimiento: para corregir hay que capturar el contrario.

**Las incógnitas:**

1. ¿Cuántas cajas hay, de cuánto, y quién responde por cada una?
2. ¿Quién puede gastar y hasta qué monto sin pedir permiso?
3. ¿Hoy alguien autoriza el gasto antes de capturarlo?
4. ¿Quién repone la caja y con qué autorización?
5. ¿Qué formato necesita el contador y cada cuándo se lo entregan?
6. ¿Se hace arqueo o conteo físico de la caja? Hoy el sistema no lo registra ni lo compara.
7. ¿Hay cierre de periodo mensual? Hoy la caja es un flujo continuo que nunca cierra.

---

## 6. `12_proceso_mantenimiento.mmd` — del activo al plan cumplido

**El recorrido.** Se da de alta el activo (camión, clima, equipo) con su clave única, placas o número
de serie, ubicación y responsable. Se le define un **plan**, y aquí está lo más interesante del
módulo: un plan puede medirse por **días, por kilómetros y por horas a la vez**, y **vence lo que
ocurra primero**. VERIFICADO. Los umbrales de "ya viene" son 15 días, 500 km y 50 horas.

El odómetro **solo puede subir**: si alguien captura una lectura menor, el sistema la rechaza con un
error. VERIFICADO. Es una protección sensata contra errores de dedo, y tiene una consecuencia práctica
que conviene saber: **si nadie captura el kilometraje, el plan por kilómetros nunca avisa.** El plan por
días sí avisa solo, porque el calendario avanza sin que nadie lo teclee.

Cuando el plan se acerca a su vencimiento, el sistema avisa a Mantenimiento y al responsable del plan.
**No crea la orden de trabajo solo**: alguien tiene que decidir. Al cerrar la orden con su costo, fecha
y lectura, el sistema **reprograma el plan desde lo realmente hecho**, no desde lo que estaba
programado. Esa es la parte que hace que el plan no se desfase con el tiempo.

**Tres huecos que encontré en este módulo**, todos VERIFICADOS leyendo el código:

1. **Una orden de trabajo no se puede cancelar desde la pantalla.** La función existe en el servicio y
   pide motivo, pero **ninguna ruta la invoca**: no hay botón ni dirección que llegue a ella. Lo mismo
   pasa con desactivar un plan.
2. **El estado "en proceso" es inalcanzable.** Está declarado en el código y en la base, pero ninguna
   función lo asigna: una orden solo puede estar abierta, cerrada o cancelada.
3. **El mantenimiento no descuenta refacciones del inventario**, y el costo se guarda como un total sin
   desglosar mano de obra y piezas.

**Las incógnitas:** ¿qué inventario de equipos existe hoy y quién lo lleva? ¿Hay programas de
mantenimiento escritos o los define el mecánico por costumbre? ¿Quién captura el kilometraje y cada
cuándo? ¿Se piden cotizaciones para un servicio externo y quién lo autoriza? ¿Las refacciones se
llevan en inventario?

---

## 7. `13_proceso_avisos.mmd` — las seis reglas y cómo se apagan

Este diagrama no es un proceso de negocio: es el mecanismo que vigila a los otros cinco. Vale la pena
entenderlo porque es donde el sistema deja de ser un archivero y empieza a avisar.

**Las seis reglas**, VERIFICADAS una por una en el código, con su periodo de repetición:

| Regla | Cuándo avisa | A quién | Se repite |
|---|---|---|---|
| Contrato por vencer | 60 días antes | RRHH | Una vez por semana |
| Documento por vencer | 30 días antes | Según el dueño del archivo | Una vez por semana |
| Lote por caducar | 30 días antes, **y solo si aún hay existencia** | Almacén | Una vez por semana |
| Existencia bajo el mínimo | Al cruzar el mínimo del producto | Almacén | Una vez al día |
| Mantenimiento programado | 15 días, 500 km o 50 horas antes | Mantenimiento y el responsable | Una vez por semana |
| Tarea vencida | Al pasarse la fecha | El rol y la persona asignada | Una vez al día |

Ese detalle del lote por caducar me parece el más fino del módulo: **no avisa de lotes que ya se
acabaron**. Consulta la existencia antes de molestar a nadie.

**Cómo funciona la idempotencia** (que suena técnico y es simple): la clave de cada aviso incluye el
periodo — la semana o el día. Por eso pulsar "Revisar ahora" cinco veces el mismo día no genera cinco
avisos iguales. VERIFICADO, y además hay pruebas automáticas que lo comprueban.

**Silenciar** guarda una marca con el identificador estable del objeto (ese lote, ese contrato) sin el
periodo, por N días o para siempre, y de paso marca como leídos los pendientes. El sistema revisa el
silencio **antes** de la idempotencia, así que un aviso silenciado no gasta el turno de la semana.

**Dos cosas que conviene que sepas:**

1. **Nadie recibe nada.** El envío de correo está apagado y **no existe ningún código que envíe correo**
   en todo el proyecto. Cada aviso queda marcado "sin adaptador". Hoy los avisos solo se ven entrando
   al sistema. VERIFICADO. Ya estaba anotado como OPE-2.
2. **No hay tarea programada.** Si nadie pulsa "Revisar ahora", no se genera ningún aviso. Y ese botón
   solo lo tienen el Administrador y Administración. VERIFICADO; ya anotado como OPE-1. Juntando las
   dos: hoy el sistema **no vigila solo**, vigila cuando alguien se lo pide.

**Las incógnitas:** ¿a quién y por qué medio deberían llegar los avisos: correo, WhatsApp, o basta la
pantalla? ¿Quién los revisa cada mañana y qué pasa si nadie los ve? ¿Debe cualquier rol poder
silenciar, incluso "solo lectura"? ¿Hace falta archivar los avisos viejos?
