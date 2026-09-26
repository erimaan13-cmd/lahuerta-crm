# Manual de uso — Sistema interno Empacadora La Huerta

Septiembre 2026. Escrito para alguien que **nunca ha usado un CRM ni un sistema de inventario**. No hace
falta saber de computación: si sabes usar WhatsApp y llenar una hoja de Excel, esto te va a resultar más
fácil que eso.

Donde dice **[CAPTURA: ...]** va una imagen de pantalla que todavía no está puesta.

> **Cómo está marcada la información.** Este manual describe lo que el sistema hace hoy, comprobado en
> su código. Donde diga **PENDIENTE** es algo que falta decidir con La Huerta, y lo verás también en la
> lista final de preguntas. Si algo de este manual no coincide con lo que ves en pantalla, gana la
> pantalla: avísale a Erick.

---

## 1. Qué es este sistema

Es **la memoria ordenada de la empresa**. Guarda en un solo lugar lo que hoy vive repartido entre
correos, cuadernos, hojas de Excel y la cabeza de cada quien:

- Quién preguntó por un producto y en qué quedó la conversación.
- Qué se cotizó, a qué precio y si se ganó o se perdió.
- Qué hay en la bodega, de qué lote y cuándo caduca.
- Qué se le compró a qué proveedor y si ya llegó.
- Qué gastos salieron de la caja chica y con qué comprobante.
- A quién le toca servicio el camión y cuándo vence un contrato.

Y hace dos cosas que un cuaderno no puede: **avisa antes de que algo se venza** y **guarda quién hizo
cada cambio**, con fecha y hora.

## 2. Qué NO es este sistema

Esto es igual de importante, y conviene decirlo antes de que alguien lo espere:

| No hace | Quién lo hace |
|---|---|
| **No emite facturas.** Ni CFDI, ni timbrado, ni PDF de factura | **CONTPAQi.** Aquí solo se anota el folio de la factura que ya se emitió allá |
| **No lleva contabilidad.** No hay pólizas, cuentas contables, IVA ni centros de costo | **El contador.** De caja chica se le entrega un archivo para que él lo capture |
| **No calcula nómina.** El expediente del empleado no guarda sueldo | El sistema de nómina que use la empresa (PENDIENTE saber cuál) |
| **No manda correos.** Ni responde, ni borra, ni archiva, ni contesta al cliente | **Una persona.** El sistema lee correos y sugiere; el clic siempre es humano |
| **No cobra ni lleva cuentas por cobrar** | Administración, por fuera |
| **No reemplaza la báscula ni el conteo físico** | La bodega. El sistema guarda lo que se le captura |

Dicho en una frase: **el sistema no ejecuta, registra y recuerda.**

---

## 3. Cómo entrar

### En la computadora

1. Abre el navegador (Chrome, Edge o el que uses).
2. Escribe la dirección que te dé Erick. Si el sistema corre en la computadora de la empresa, será algo
   como `http://127.0.0.1:8000`.
3. Escribe tu correo y tu contraseña, y pulsa **Entrar**.

**[CAPTURA: la pantalla de acceso, con los campos de correo y contraseña]**

Si te equivocas cinco veces seguidas, el sistema **te bloquea 15 minutos**. No está roto: es una
protección para que nadie adivine contraseñas a fuerza de intentarlo. Espera y vuelve a intentar.

### En el celular

Igual: abre el navegador del teléfono y escribe la misma dirección. **No hay que instalar ninguna
aplicación.**

En el celular la pantalla se acomoda sola:

- El menú se esconde detrás del botón de las tres líneas, arriba a la izquierda. Tócalo y se desliza.
- Las tablas dejan de ser tablas y se vuelven **fichas**: cada renglón se convierte en un bloque con sus
  datos etiquetados, para no tener que deslizar de lado.

**[CAPTURA: la misma pantalla de inventario en computadora y en celular, una al lado de la otra]**

**Consejo:** guarda la dirección en la pantalla de inicio del teléfono. Queda como si fuera una
aplicación.

### Lo primero que conviene entender: tu rol

El sistema le asigna a cada persona un **rol**, que es su puesto dentro del sistema: Ventas, Almacén,
Recursos Humanos, etc. Tu rol decide **qué puedes cambiar**.

Algo que sorprende al principio: **casi todos ven casi todo**. El de almacén ve los clientes, y el
vendedor ve el inventario. Es a propósito, para que un vendedor pueda checar si hay producto antes de
prometer una entrega. Lo que cambia entre roles no es lo que ves, sino **lo que puedes escribir**.

Solo cuatro secciones están reservadas: **Personal** y **Caja chica** (por los datos delicados),
**Historial** y **Usuarios** (solo el administrador).

Si intentas entrar a una que no te toca, verás un mensaje de error. Hoy ese mensaje está escrito en
lenguaje técnico y es confuso; ya está anotado para arreglarse.

---

## 4. El Tablero

**Para qué sirve:** es la pantalla de inicio. Un resumen de cómo va todo.

**Quién lo usa:** todos, y hoy **todos ven exactamente el mismo**, lo cual lo hace más denso de lo
necesario para algunos puestos. Está anotado para mejorarse.

**Qué mirar primero:** los **Avisos pendientes**, arriba. Es lo único de la pantalla que exige acción.

**[CAPTURA: el tablero completo, señalando el bloque de avisos pendientes]**

**Error de novato:** creer que el tablero se actualiza solo con todo. Las tarjetas sí se calculan al
momento, pero **los avisos no se generan solos**: alguien tiene que pulsar "Revisar ahora" en la
pantalla de Avisos. Es la cosa más importante de este manual, y está explicada en el capítulo 15.

---

# PARTE I · Lo comercial

## 5. Prospectos

**Para qué sirve:** guardar a **toda persona que pregunta**, aunque todavía no sea cliente.

**Quién escribe aquí:** Ventas y Atención a clientes.

Un **prospecto** es la *persona* que preguntó. No confundir con **Cliente potencial**, que es la
*empresa* que todavía no ha comprado. Persona y empresa son cosas distintas en el sistema.

### Tarea 1: dar de alta a alguien que acaba de preguntar

1. Menú → **Prospectos**.
2. Abajo, en **Nuevo prospecto**, llena lo que sepas. Solo el nombre es obligatorio; lo demás se puede
   completar después.
3. Pulsa el botón de guardar.

El sistema **te crea sola una tarea de primer contacto, con vencimiento a 4 horas hábiles**. Hábiles
quiere decir de lunes a viernes de 8 a 17, hora de Monterrey, y sin contar días festivos: si alguien
pregunta un viernes a las 16:30, la tarea vence el lunes, no el sábado.

**[CAPTURA: el formulario de Nuevo prospecto]**

### Tarea 2: registrar que ya le llamaste

1. Abre el prospecto desde la lista.
2. En la sección de actividades, registra la llamada con lo que quedó.
3. El prospecto pasa a **contactado**.

### Tarea 3: convertirlo en cliente

Cuando el prospecto ya está **calificado** (interesa y el volumen alcanza), aparece el botón
**Convertir**. Con un solo clic el sistema crea tres cosas: la **Cuenta** (la empresa), el **Contacto**
(la persona dentro de esa empresa) y una **Oportunidad** (la venta que se va a perseguir).

**Solo Ventas puede convertir.** Atención a clientes da de alta el prospecto, pero el paso de convertir
lo hace Ventas.

**Qué no puede hacer aquí:** borrar un prospecto. Se **descarta** con un motivo, y queda guardado. Nada
se borra en este sistema, nunca.

**Errores de novato:**
- Dar de alta dos veces a la misma persona. El sistema detecta el correo repetido y marca el posible
  duplicado, pero **no los une solo**: hay que pulsar "Fusionar".
- Creer que "descartado" es "borrado". Sigue ahí, y se puede filtrar en la lista.

## 6. Cuentas y contactos

**Para qué sirve:** la ficha de cada empresa cliente y de las personas que trabajan en ella.

**Quién escribe aquí:** Ventas.

Cada cuenta tiene un **estado**: *Cliente potencial* (todavía no compra), *Cliente activo*, y otros. Lo
importante es que **el sistema mueve ese estado solo**: cuando se entrega el primer pedido, la cuenta
pasa de Cliente potencial a Cliente activo sin que nadie lo teclee.

**Qué mirar:** al abrir una cuenta la ves completa — sus oportunidades, sus pedidos, sus casos, sus
correos y todo lo que se ha platicado con ella. Es la pantalla que conviene tener abierta antes de
llamarle a un cliente.

**[CAPTURA: la vista de una cuenta con sus oportunidades y pedidos]**

## 7. Oportunidades

**Para qué sirve:** seguirle la pista a cada venta desde que el cliente pregunta hasta que se gana o se
pierde.

**Quién escribe aquí:** Ventas.

Una **oportunidad** es una venta posible, con nombre y monto estimado. Se mueve por **etapas**, que son
los pasos por los que va pasando. Hay ocho:

| Etapa | Qué significa |
|---|---|
| Requerimiento | El cliente ya dijo qué necesita y cuántos kilos |
| Desarrollo de fórmula | Hay que formular una mezcla especial para él |
| Muestra enviada | Se le mandó producto para que lo pruebe |
| Muestra aprobada | Dijo que sí, la muestra sirve |
| Cotización | Ya hay precio por escrito |
| Negociación | Está pidiendo descuento o cambiando condiciones |
| Ganada | Se convirtió en pedido |
| Perdida | No compró, y se anota por qué |

**Saltarse etapas es normal y el sistema lo permite.** Una recompra de producto de catálogo va de
Requerimiento directo a Cotización: no hay que inventar una muestra que nunca existió.

La pantalla es un **tablero de columnas** (una por etapa) con tarjetas. Ver dónde se acumulan las
tarjetas es el punto: si hay ocho en "Muestra enviada" y ninguna en "Muestra aprobada", **nadie está
dando seguimiento a las muestras**.

**[CAPTURA: el tablero de oportunidades por etapa]**

### Tarea común: hacer una cotización

1. Abre la oportunidad.
2. Crea la cotización con sus renglones y precios.
3. Pulsa para generar el **PDF**, que trae su folio.
4. **Descárgalo y mándalo tú** por correo o WhatsApp. El sistema no lo envía.
5. Regresa y pulsa **Marcar enviada**. Eso le dice al sistema que ya salió, y te crea la tarea de
   seguimiento.

**Qué no puede hacer:** enviar la cotización. Y **no valida el precio**: puedes guardar un renglón en
cero y nadie te va a avisar. PENDIENTE: quién autoriza un descuento.

## 8. Pedidos

**Para qué sirve:** registrar lo que el cliente compró y **descontarlo del inventario** al entregarlo.

**Quién escribe aquí:** Ventas y Administración. **Quien entrega suele ser Almacén.**

Un pedido pasa por cuatro estados: **borrador → confirmado → entregado**, o **cancelado**.

### Tarea 1: capturar el pedido

Menú → **Pedidos** → nuevo. Se captura la cuenta, la bodega de donde saldrá, la fecha prometida y los
renglones **en kilos**.

### Tarea 2: confirmar

Pulsa **Confirmar**. El sistema revisa que haya existencia.

> **OJO, esto es importante:** confirmar **revisa pero no aparta**. El producto sigue disponible para
> otro pedido. Si dos vendedores confirman pedidos sobre los mismos kilos, los dos pasan, y el conflicto
> aparece hasta que alguien intente entregar. PENDIENTE de decidir; está anotado como riesgo.

### Tarea 3: entregar

Pulsa **Entregar**. Aquí pasan tres cosas de golpe:

1. El sistema **descuenta el inventario**, y **sale primero el lote que caduca antes**. Esa decisión la
   toma el sistema; nadie tiene que elegir el lote a mano.
2. Es **todo o nada**: si falta producto en un solo renglón, no se descuenta ninguno y el pedido se
   queda como estaba. No existe la entrega parcial.
3. Si era el primer pedido de esa cuenta, pasa a **Cliente activo**.

**[CAPTURA: un pedido entregado mostrando los movimientos de inventario que generó]**

### Tarea 4: anotar el folio de la factura

Cuando CONTPAQi ya emitió la factura, se captura aquí **solo el folio**. El sistema no factura ni
verifica el folio: lo guarda como referencia.

**Qué no puede hacer Pedidos:** facturar, cobrar, apartar producto, entregar a medias, registrar una
devolución, ni guardar dirección de entrega o guía del transportista.

**Errores de novato:**
- Creer que confirmar aparta el producto. No lo aparta.
- Intentar entregar un borrador. Hay que confirmarlo primero.
- Buscar cómo deshacer una entrega. **No se puede**: "entregado" es final. Un error se corrige con un
  ajuste de inventario, y eso lo hace Almacén.

## 9. Correos

**Para qué sirve:** leer el buzón, **clasificar solo** cada mensaje y sugerir qué hacer con él.

**Quién escribe aquí:** Atención a clientes y Administración.

El sistema lee y propone; **nunca actúa solo**. No responde, no borra, no archiva y no mueve nada en el
buzón. Cada sugerencia se aplica con un clic humano.

### Las dos formas de meter correos

- **Cargar correos de ejemplo:** trae un buzón de demostración que viene incluido. Es **solo para
  practicar**; no toca ningún buzón real.
- **Subir un archivo `.eml`:** un `.eml` es lo que se genera cuando guardas un correo como archivo desde
  Outlook o Gmail. Sirve para probar el clasificador con un correo real sin conectar el buzón.

### La bandeja "Needs Review"

Cuando el sistema no está seguro de cómo clasificar un correo, **no adivina**: lo manda a esa bandeja
para que una persona decida. Que un correo caiga ahí no es una falla, es el diseño.

**[CAPTURA: un correo clasificado, mostrando las entidades detectadas y el botón Aplicar]**

**Errores de novato:**
- Pensar que "Cargar correos de ejemplo" va a traer el correo real de la empresa. No: son de práctica.
- Esperar que el sistema conteste. No contesta. PENDIENTE: quién responde y con qué.

## 10. Casos

**Para qué sirve:** llevar un problema del cliente hasta resolverlo. Sobre todo **reclamaciones de
calidad**.

**Quién escribe aquí:** Calidad, Atención a clientes y Ventas.

Lo específico de este módulo: una reclamación de calidad **necesita el número de lote** para poder
resolverse. Con ese número, Calidad puede buscar en inventario cuánto queda de ese lote y ver, por los
movimientos de salida, **a qué otros clientes se les vendió el mismo lote**. Eso es el rastreo que pide
la certificación FSSC 22000, y hoy funciona.

**Qué no puede hacer:** bloquear un lote sospechoso para que no se venda (no existe), impedir la venta
de un lote caducado (no la impide), ni registrar la devolución del producto. PENDIENTES los tres.

**Error de novato:** cerrar un caso sin anotar el lote. El sistema lo exige para las reclamaciones de
calidad, y con razón: sin lote no hay rastreo.

---

# PARTE II · La operación

## 11. Inventario

**Para qué sirve:** saber **cuánto hay, de qué lote, en qué bodega y cuándo caduca**.

**Quién escribe aquí:** Almacén y Abastecimiento.

### La idea que hay que entender antes de tocar nada

**El sistema no guarda un número de existencia.** Guarda **movimientos**: entradas y salidas. La
existencia es la suma de todos ellos, y se recalcula cada vez que la consultas.

Suena rebuscado y es lo contrario: significa que **la existencia siempre se puede explicar**. Si dice
340 kg, hay una lista de movimientos que suman 340, cada uno con su fecha, su motivo y quién lo hizo. Un
número guardado a mano se desincroniza y nadie sabe cuándo empezó a mentir.

De ahí sale la otra regla: **la existencia nunca puede quedar negativa.** Si intentas sacar más de lo
que hay, el sistema no te deja.

### Los cuatro tipos de movimiento

| Tipo | Cuándo se usa |
|---|---|
| **Entrada** | Llegó mercancía. La mayoría vienen solas de una recepción de compra |
| **Salida** | Salió mercancía. La mayoría vienen solas de la entrega de un pedido |
| **Ajuste** | Corregir una diferencia. **Exige motivo obligatorio** |
| **Traspaso** | Pasar producto de una bodega a otra. Genera dos movimientos, una salida y una entrada |

### Tarea 1: ver qué hay

Menú → **Inventario**. Verás las existencias por producto, lote y bodega, con la caducidad marcada por
color cuando está cerca.

**[CAPTURA: la pantalla de inventario con un lote marcado por caducar]**

### Tarea 2: capturar un movimiento a mano

Se usa cuando algo entró o salió sin pasar por un pedido ni por una compra. Elige el tipo, el producto,
la bodega, los kilos y **el lote**.

> **Captura siempre el lote.** El sistema te deja guardar una salida sin lote, y cuando lo haces la
> cuenta total queda bien pero **el lote sigue diciendo que tiene lo que ya salió**. Se pierde el
> rastreo, que es justo lo que se necesita cuando hay una reclamación. Ya está anotado para arreglarse;
> mientras tanto, es disciplina de captura.

### Tarea 3: hacer un ajuste

Igual que un movimiento, con tipo **Ajuste**, y el sistema **te obliga a escribir el motivo**. Escribe
algo que se entienda en seis meses: "conteo físico del 15 de marzo, faltaban 3 kg", no "corrección".

**Qué no puede hacer Inventario:** no valora el inventario en pesos, no registra conteos físicos como
tal (solo el ajuste que resulta), no impide vender un lote caducado, y **ningún movimiento se puede
borrar ni editar**. Para corregir, otro movimiento.

**Errores de novato:**
- Buscar dónde "poner" la existencia correcta. No se pone: se captura el movimiento que falta.
- Capturar una salida sin lote (ver el aviso de arriba).
- No poner motivo en un ajuste y no entender por qué no guarda.

## 12. Abastecimiento

**Para qué sirve:** las órdenes de compra a proveedores, y **meter la mercancía al inventario cuando
llega**.

**Quién escribe aquí:** Abastecimiento y Administración. **Quien autoriza es solo el administrador.**

Una orden pasa por: **borrador → por autorizar → autorizada → recibida**, o **cancelada**.

### Tarea 1: crear la orden

Menú → **Abastecimiento** → Nueva orden de compra. Se elige el proveedor y se capturan los renglones en
kilos con su costo. Queda en **borrador**, editable.

Al abrir el proveedor puedes ver **el historial de precios que le has pagado**. Sirve para saber si lo
que te está cotizando hoy es caro.

### Tarea 2: enviarla

Pulsa **Enviar**. Aquí el sistema decide solo:

- Si el total **no pasa de $20,000**, queda **autorizada** de una vez.
- Si **pasa de $20,000**, queda **por autorizar** y hay que esperar al administrador.

Ese monto es un valor provisional. PENDIENTE de confirmar.

**Autorizar es exclusivo del administrador, y es a propósito:** quien crea la orden no debe poder
aprobarla. Si Abastecimiento tuviera esa llave, aprobaría sus propias compras.

**[CAPTURA: una orden en estado "por autorizar", con el botón de autorizar visible solo para el administrador]**

### Tarea 3: recibir la mercancía

Cuando llega el producto, pulsa **Recibir** y captura, renglón por renglón: los kilos que de verdad
llegaron, la bodega, y **el código de lote que viene en el costal o la etiqueta**.

- **El código de lote es obligatorio.** Sin él no se puede recibir. Es lo que sostiene todo el rastreo.
- **La caducidad es opcional.** Si no la capturas y el producto tiene vida útil definida, el sistema la
  calcula sumando los días a la fecha de recepción.
- **Se puede recibir a medias:** deja en cero los renglones que no llegaron. La orden se queda abierta y
  puedes recibir el resto después. Solo cuando llega todo pasa a **recibida**.

Al recibir, el sistema crea el lote (o usa el que ya existía) y mete la **entrada** al inventario.

**Qué no puede hacer Abastecimiento:** mandarle la orden al proveedor (no envía nada: hay que llamarle o
escribirle), registrar pagos o plazos, manejar IVA, flete o moneda extranjera, guardar datos fiscales
del proveedor, ni registrar mercancía rechazada o devuelta. PENDIENTE lo del rechazo.

**Errores de novato:**
- Esperar que el proveedor reciba la orden. No la recibe: el sistema no la manda.
- Inventar un código de lote porque el costal no lo trae. Mejor pregunta al proveedor: un lote inventado
  rompe el rastreo el día que haya una queja.
- Cancelar una orden ya recibida creyendo que se deshace la entrada. **No se deshace**: la mercancía ya
  entró al inventario.

## 13. Mantenimiento

**Para qué sirve:** que no se te pase el servicio de un camión ni la verificación de un equipo.

**Quién escribe aquí:** Mantenimiento.

Tres conceptos: el **activo** (el camión, el clima, el equipo), el **plan** (cada cuándo le toca) y la
**orden de trabajo** (el servicio concreto que se hizo o se va a hacer).

### Lo que hace especial a este módulo

Un plan se puede medir por **días, por kilómetros y por horas al mismo tiempo**, y **vence lo que ocurra
primero**. Un camión puede tener "cada 6 meses o cada 10,000 km, lo que llegue antes".

### Tarea 1: capturar el kilometraje

Abre el activo y captura la lectura del odómetro.

> **Esto es lo más importante del módulo.** La lectura **solo puede subir**: si capturas un número menor
> el sistema lo rechaza, para protegerte de un error de dedo. Y tiene una consecuencia: **si nadie
> captura el kilometraje, el plan por kilómetros nunca avisa.** El plan por días sí avisa solo, porque
> el calendario avanza sin que nadie lo teclee. PENDIENTE: quién lo captura y cada cuándo.

### Tarea 2: abrir una orden de trabajo

Cuando toca servicio, o cuando algo se rompió, abre la orden: si es **preventivo** (lo programado) o
**correctivo** (se falló), y si lo hace el taller **interno** o un proveedor **externo**.

### Tarea 3: cerrar la orden

Al terminar, captura el costo, la fecha, el kilometraje y las notas. El sistema **reprograma el plan
desde lo que realmente se hizo**, no desde lo que estaba programado. Así el plan no se desfasa con los
meses.

**[CAPTURA: la ficha de un camión con su plan por kilometraje y su historial de órdenes]**

**Qué no puede hacer:** crear la orden sola cuando un plan vence (avisa, pero alguien decide),
descontar refacciones del inventario, desglosar mano de obra y piezas, y **hoy no se puede cancelar una
orden desde la pantalla** ni marcarla "en proceso". Los tres últimos están anotados.

## 14. Tareas

**Para qué sirve:** que no se te olvide lo que quedaste de hacer, y poder pedirle algo a otra área.

**Quién escribe aquí:** todos los roles menos "solo lectura".

Una tarea tiene responsable, fecha de vencimiento y estado. Puede estar asignada a **una persona** o a
**un área completa** (por ejemplo "Ventas"), lo cual sirve cuando cualquiera del área puede atenderla.

**Lo que conviene saber:** el sistema **crea tareas solo** en tres momentos, sin que nadie las teclee:

1. Al dar de alta un prospecto → tarea de primer contacto, a 4 horas hábiles.
2. Al ganar una oportunidad → tarea para Administración.
3. Al marcar una cotización como enviada → tarea de seguimiento.

Las fechas de vencimiento respetan **horario hábil**: lunes a viernes de 8 a 17, hora de Monterrey, sin
festivos. Una tarea creada el viernes a las 16:30 con 4 horas de plazo vence el lunes.

Cuando una tarea se pasa de su fecha, genera un **aviso** para quien la tenga asignada — siempre y cuando
alguien haya pulsado "Revisar ahora" (ver el capítulo siguiente).

**[CAPTURA: la lista de tareas filtrada por pendientes, con una vencida marcada]**

**Qué no puede hacer:** no manda recordatorios por correo, y no hay subtareas ni dependencias entre
tareas.

**Error de novato:** cerrar una tarea sin registrar lo que se hizo. La tarea desaparece de la lista, pero
la actividad —la llamada, el correo, el acuerdo— es lo que le sirve al que atienda a ese cliente después.
Regístrala en la cuenta o el prospecto.

## 15. Avisos — el capítulo que hay que leer completo

**Para qué sirve:** que el sistema te diga lo que se está por vencer antes de que te cueste dinero.

**Quién lo ve:** todos, cada uno los de su área.

### Las seis cosas que vigila

| Aviso | Cuándo aparece | A quién |
|---|---|---|
| Contrato por vencer | 60 días antes | Recursos Humanos |
| Documento por vencer | 30 días antes | Al área dueña del documento |
| Lote por caducar | 30 días antes, **y solo si todavía hay existencia** | Almacén |
| Existencia bajo el mínimo | Al cruzar el mínimo del producto | Almacén |
| Mantenimiento programado | 15 días, 500 km o 50 horas antes | Mantenimiento |
| Tarea vencida | Al pasarse la fecha | A quien la tenga asignada |

Detalle fino: el aviso de lote por caducar **no molesta con lotes que ya se acabaron**. Consulta la
existencia antes de avisar.

### Lo que tienes que saber, aunque incomode

**El sistema no vigila solo. Vigila cuando alguien se lo pide.**

1. **No hay tarea programada.** Los avisos se generan cuando alguien pulsa **Revisar ahora**. Si nadie
   lo pulsa, el lote que caduca en 30 días no avisa a nadie.
2. **Ese botón solo lo tienen el administrador y Administración.** Ni Almacén, ni Mantenimiento, ni RRHH
   pueden generar los avisos que van dirigidos a ellos mismos.
3. **No sale por correo.** Cada aviso queda marcado "sin adaptador" y solo se ve entrando al sistema.

**Mientras esto no se arregle, alguien tiene que pulsar "Revisar ahora" todos los días.** Es la
recomendación más práctica de este manual. Ya está anotado como el segundo riesgo más grave del sistema.

**[CAPTURA: la pantalla de avisos con el botón "Revisar ahora" señalado]**

### Cómo apagar un aviso

- **Marcar leído:** lo quitas de pendientes.
- **Silenciar:** no vuelve a aparecer durante los días que digas, o para siempre. Sirve para el lote que
  ya sabes que vas a rematar y no quieres que te lo recuerden cada semana.

Pulsar "Revisar ahora" cinco veces el mismo día **no genera cinco avisos iguales**: el sistema sabe que
ya avisó de eso en este periodo.

**Error de novato:** silenciar un aviso para siempre por quitárselo de encima. Silenciar el lote de un
producto apaga ese recordatorio de forma permanente. Usa días.

---

# PARTE III · Lo reservado

## 16. Personal

**Para qué sirve:** el expediente de cada empleado y el control de sus contratos.

**Quién entra:** **solo Recursos Humanos y el administrador.** Cada consulta queda registrada.

Guarda: número de empleado, nombre, área, puesto, fecha de ingreso, teléfono, correo, notas y los
documentos escaneados (contrato, identificación, certificados).

El **puesto** describe funciones y requisitos, uno por renglón. A pesar de lo que decía un documento
anterior, **no es un sistema de puntos ni una valuación**: son viñetas.

### Las tres tareas

1. **Dar de alta el expediente** con el número de empleado (único) y el nombre.
2. **Registrar el contrato**: temporal o indeterminado, con sus fechas. **Solo puede haber un contrato
   vigente por persona.** Sube el PDF escaneado.
3. **Renovar o terminar** cuando el aviso llegue a 60 días. Al renovar, el anterior queda marcado como
   renovado y nace uno nuevo: la cadena completa queda guardada.

Un contrato **indeterminado no vence y por tanto nunca avisa**. Solo los temporales avisan.

Al dar de baja a alguien se exige motivo, se cierran sus contratos y **nada se borra**.

**[CAPTURA: un expediente con su contrato y la alerta de vencimiento]**

**Qué no puede hacer:** calcular nómina (no guarda sueldo), registrar asistencia, vacaciones o
incidencias, emitir contratos en PDF, ni conectarse con IMSS o SAT.

> **Antes de cargar expedientes reales hace falta el aviso de privacidad firmado.** No es un detalle
> técnico: es un requisito legal. Mientras no exista, el módulo debe usarse solo con datos de prueba.

## 17. Caja chica

**Para qué sirve:** llevar el efectivo con su comprobante y entregarle al contador un archivo limpio.

**Quién entra:** **solo Administración y el administrador.**

**El saldo** se calcula así: monto del fondo, más las reposiciones, menos los gastos. No hay un número
guardado: se recalcula cada vez.

### Las tres tareas

1. **Registrar un gasto:** monto, categoría, descripción y **el comprobante, que es obligatorio**. Sin
   archivo adjunto el gasto no se guarda. Se acepta PDF, foto, XML o texto de hasta 15 MB. El sistema
   **guarda el archivo pero no lee lo que dice**: el monto lo capturas tú.
2. **Registrar una reposición** cuando se acabe el efectivo. Aquí el comprobante es opcional.
3. **Exportar el CSV** para el contador. Un CSV es un archivo de tabla que abre en Excel.

Si un gasto no cabe en el saldo, el sistema lo rechaza: **el saldo nunca queda negativo**.

**[CAPTURA: el registro de un gasto con el campo de comprobante obligatorio]**

**Qué no puede hacer:** contabilizar (ni pólizas, ni cuentas, ni IVA), emitir recibos, **autorizar
gastos** (no hay ningún flujo de aprobación, a diferencia de compras), hacer arqueos, ni cerrar el mes.
Y **ningún movimiento se puede editar ni borrar**: para corregir, se captura el contrario.

**Error de novato:** subir el comprobante y creer que el sistema leyó el monto del ticket. No lo lee. Si
te equivocas al teclear el monto, el saldo queda mal y solo se corrige con otro movimiento.

## 18. Documentos

**Para qué sirve:** ver de un tirón **todo lo que está por vencerse**: pólizas, seguros,
verificaciones, contratos escaneados.

**Quién lo ve:** todos, **pero cada quien solo los documentos de los módulos que puede leer**. Un
documento de un expediente lo ven RRHH y el administrador; un comprobante de caja, Administración y el
administrador.

El sistema **guarda los archivos tal cual y nunca los lee**. No hay lectura automática de texto: si un
documento tiene vencimiento, alguien lo captura y entonces el sistema avisa.

**Qué no puede hacer:** borrar un documento (para no perder evidencia), editarlo después de subirlo, ni
leer su contenido.

## 19. Historial

**Para qué sirve:** saber **quién hizo qué, cuándo y desde dónde**. Es la razón de ser del sistema para
una empresa que necesita auditar.

**Quién lo ve:** **solo el administrador.**

Se registra **cada acción de cada usuario**: no solo los cambios, también las consultas, las descargas,
los inicios de sesión y los intentos rechazados. Y nadie, ni el administrador, puede editar o borrar un
renglón del historial: el sistema no tiene ninguna función para hacerlo.

Los tres filtros que parecen lo mismo y no lo son:

- **Tipo de evento:** la naturaleza de lo ocurrido (cambios de datos, consultas, seguridad, sistema).
- **Sobre qué registro:** en qué vive el evento (un prospecto, una cuenta, un pedido, una pantalla).
- **El nombre técnico del evento:** búsqueda libre sobre el identificador interno. Es para quien audita
  el código, no para el uso diario.

La columna **Detalle** es lo importante: dice qué cambió, en la forma `etapa: nuevo → contactado`.

El **usuario** de cada renglón se guarda como el correo **congelado al momento del evento**: si alguien
cambia de nombre o de área, su historial anterior no se reescribe.

**[CAPTURA: el historial filtrado por usuario, señalando la columna Detalle]**

## 20. Usuarios

**Para qué sirve:** dar de alta y de baja personas, cambiarles el área y la contraseña.

**Quién entra:** **solo el administrador.** Todo cambio queda en el historial.

---

# Glosario

Una línea por término. Están en el orden en que te los vas a topar.

| Término | Qué es |
|---|---|
| **Prospecto** | La **persona** que preguntó por un producto y todavía no es cliente |
| **Cliente potencial** | La **empresa** registrada que todavía no ha comprado nada |
| **Oportunidad** | Una venta posible que se está persiguiendo, con su monto estimado |
| **Etapa** | El paso en que va una oportunidad (Requerimiento, Cotización, Ganada…) |
| **Cotización** | El precio por escrito, con folio y vigencia, que se le manda al cliente |
| **Lote** | El conjunto de producto que llegó junto y comparte código y caducidad; es lo que permite rastrear de dónde salió algo |
| **Caducidad** | La fecha a partir de la cual el producto ya no debe venderse |
| **Movimiento de inventario** | Cada entrada o salida de producto. La existencia es la suma de todos los movimientos, no un número guardado |
| **Bitácora** (o Historial) | El registro de quién hizo qué y cuándo. Solo se agrega: nunca se edita ni se borra |
| **Rol** | El puesto que el sistema te asigna (Ventas, Almacén, RRHH…) y que decide qué puedes cambiar |
| **Permiso** | Una llave suelta dentro de un rol, por ejemplo "puede leer caja chica". Un rol es un manojo de llaves |
| **.eml** | Un correo guardado como archivo. Es lo que genera Outlook o Gmail al guardar un mensaje |
| **CFDI** | La factura electrónica válida ante el SAT. **Este sistema no la emite**: la emite CONTPAQi y aquí solo se anota su folio |
| **Folio** | El número que identifica un documento. Unos los genera el sistema (`COT-`, `PED-`, `OC-`, `OM-`) y otros se capturan de fuera, como el de la factura |

---

# Preguntas abiertas para La Huerta

Esta lista importa tanto como el manual. Son las cosas que **no se pueden contestar leyendo el sistema**
y que cambian decisiones. Agrupadas por módulo.

### Prospectos y correos
1. ¿Quién atiende cada canal hoy — web, WhatsApp, teléfono, correo — y en cuánto tiempo se responde?
2. ¿Sigue habiendo un solo buzón (`administracion@`)? ¿Quién lo abre?
3. ¿Cuántos correos llegan al día? Define si bastan las reglas actuales.
4. ¿Sigue vigente el mínimo de 500 kg para calificar a un cliente?
5. ¿Quién le contesta al cliente, y con qué? El sistema no responde correos.

### Oportunidades y cotizaciones
6. ¿Se usan de verdad las etapas "Desarrollo de fórmula" y "Muestra aprobada", o conviene juntarlas con
   las vecinas?
7. **¿Quién autoriza un descuento o un precio especial?** Hoy el sistema acepta cualquier precio,
   incluso cero, sin avisar.
8. ¿Se necesitan versiones de una misma cotización (v2, v3) durante la negociación?

### Pedidos
9. **Cuando confirman un pedido, ¿apartan el producto físicamente en la bodega, o se surte hasta el día
   de la salida? ¿Ha pasado que dos pedidos prometan el mismo producto y no alcance?**
10. **¿Les pasa que surten un pedido a medias? Si sí, ¿cómo lo registran y cómo sabe el cliente qué le
    queda pendiente?**
11. ¿Quién captura el pedido: el vendedor o Administración?
12. ¿Quién captura el folio de la factura, y en qué momento: al facturar o al cobrar?
13. ¿El reparto es propio o por paquetería? ¿Se firma evidencia de entrega?
14. ¿El sistema debería avisar de facturas por cobrar? Hoy no lleva cobranza.

### Inventario
15. **Cuando un cliente les regresa mercancía, o cuando el proveedor manda producto que no pasa calidad,
    ¿qué hacen con esos kilos: los vuelven a meter al almacén, los separan, los tiran? ¿Quién lo anota?**
16. ¿Con qué frecuencia hacen conteo físico, y quién puede ajustar una diferencia?
17. ¿Qué hacen hoy con un lote que ya caducó? El sistema no impide venderlo.
18. ¿Debería poderse **bloquear** un lote sospechoso para que no salga? Hoy no existe.
19. ¿Se maneja producto en sacos y cajas además de kilos?

### Abastecimiento
20. ¿Quién revisa el aviso de existencia baja, y cada cuándo?
21. ¿Se compra por mínimos, por temporada, o cuando lo pide producción?
22. **¿Cómo le avisa hoy Almacén a Abastecimiento que hay que comprar?** El sistema no tiene mensajes
    entre áreas.
23. ¿Se piden varias cotizaciones antes de comprar? El sistema no las guarda.
24. **¿El umbral de $20,000 para pedir autorización es el real?**
25. **¿Quién aprueba las compras: el dueño, o hace falta un jefe de compras que autorice sin poder crear
    órdenes?**
26. ¿Quién recibe en el andén y quién revisa calidad y caducidad?
27. ¿Se rechaza un lote con poca vida útil? ¿Cuál es el mínimo aceptable?
28. ¿Hay importaciones en otra moneda?

### Mantenimiento
29. **¿Quién captura el kilometraje de los camiones, y cada cuándo?** Sin eso, los planes por kilómetros
    no avisan.
30. ¿Qué equipos existen hoy y quién los lleva?
31. ¿Hay programas de mantenimiento escritos, o los define el mecánico por costumbre?
32. ¿Se piden cotizaciones para un servicio externo, y quién lo autoriza?
33. ¿Las refacciones se llevan en inventario? Hoy el mantenimiento no descuenta piezas.

### Personal
34. **¿Existe ya el aviso de privacidad firmado?** Es obligatorio antes de cargar expedientes reales.
35. ¿Hacen falta RFC, CURP, NSS, domicilio y salario en el expediente? Hoy no se guardan.
36. ¿Se necesita reporte de rotación? Hoy la fecha y el motivo de baja van en notas libres.
37. ¿Con qué sistema se calcula la nómina?
38. ¿Se lleva asistencia, vacaciones o incidencias en algún lado?
39. ¿Existen descripciones de puesto escritas?

### Caja chica
40. ¿Cuántas cajas hay, de cuánto, y quién responde por cada una?
41. ¿Quién puede gastar y hasta qué monto sin pedir permiso?
42. ¿Hoy alguien autoriza el gasto antes de capturarlo? El sistema no tiene aprobación.
43. ¿Quién repone la caja y con qué autorización?
44. ¿Qué formato necesita el contador, y cada cuándo se lo entregan?
45. ¿Se hace arqueo o conteo físico de la caja?
46. ¿Hay cierre de periodo mensual? Hoy la caja es un flujo continuo.

### Avisos
47. **¿Quién va a pulsar "Revisar ahora" todos los días?** O se programa para que corra solo.
48. ¿A quién y por qué medio deberían llegar los avisos: correo, WhatsApp, o basta la pantalla?
49. ¿Debe cualquier rol poder silenciar un aviso, incluso "solo lectura"?

### Roles y uso
50. ¿Existen de verdad las diez áreas, o una sola persona cubre varias?
51. ¿Quién trabajará en computadora y quién en celular?
52. ¿El director quiere ver el historial sin poder editar nada?
53. ¿Qué número quiere ver primero el director al entrar?

### Calidad
54. ¿Qué procedimiento siguen hoy ante una reclamación, y quién decide si se repone o se bonifica?
55. ¿Esto reemplaza un sistema de calidad o convive con uno? El sistema **no es un QMS**: las no
    conformidades se llevan como casos.
56. ¿Qué pide FSSC 22000 que hoy no esté cubierto?
