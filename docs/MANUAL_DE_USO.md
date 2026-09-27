# Manual de uso — Sistema interno Empacadora La Huerta

Septiembre 2026. Escrito para alguien que **nunca ha usado un CRM ni un sistema de inventario**. No hace
falta saber de computación: si sabes usar WhatsApp y llenar una hoja de Excel, esto te va a resultar más
fácil que eso.

Donde dice **[CAPTURA: ...]** va una imagen de pantalla que todavía no está puesta.

## Lo primero, porque cambia cómo se usa todo lo demás

> ### En este sistema nada se corrige borrando. Cada error se arregla con un registro nuevo encima.
>
> No hay botón de borrar, y no es un olvido: es la decisión de fondo del sistema. Un prospecto mal
> capturado se descarta con su motivo; una existencia equivocada se corrige con un movimiento de ajuste;
> un gasto mal capturado se compensa con otro movimiento. Todo queda, y queda a nombre de quien lo hizo.
>
> Si vienes de trabajar en Excel, esto es el cambio más grande: ahí corriges la celda y nadie se entera.
> Aquí la corrección **también es un hecho registrado**. Suena incómodo y es la razón por la que este
> sistema sirve para responder "¿quién cambió esto y cuándo?" — que es justo lo que un cuaderno o una
> hoja de cálculo no pueden.

> **Cómo está marcada la información.** Este manual describe lo que el sistema hace hoy, comprobado en
> su código. Donde diga **PENDIENTE** es algo que falta decidir con La Huerta. Si algo de este manual no
> coincide con lo que ves en pantalla, gana la pantalla: avisa a quien administra el sistema.

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
2. Escribe la dirección que te dé quien administra el sistema. Guárdala en favoritos la primera vez y ya
   no tendrás que volver a preguntarla.
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

### La regla que sostiene todo lo demás: tu cuenta es tuya

> **No compartas tu contraseña, y no uses la cuenta de otra persona. Nunca.**
>
> Esto no es una recomendación de seguridad genérica: es lo que hace que el sistema sirva. Todo lo que
> este manual promete —saber quién cambió una existencia, quién autorizó una compra, quién consultó un
> expediente— **se apoya en que cada sesión sea de una sola persona**. Si dos personas usan la misma
> cuenta, el historial sigue registrando todo con precisión… y atribuyéndoselo a la persona equivocada.
> Eso queda **peor que no tener historial**, porque parece confiable y no lo es.
>
> Si alguien más necesita entrar, pídele al administrador que le dé su propia cuenta. Toma un minuto.

---

## 4. Tu rol: qué puedes ver y qué puedes cambiar

El sistema le asigna a cada persona un **rol**, que es su puesto dentro del sistema. Hay diez.

**Lo que sorprende al principio: casi todos ven casi todo.** El de almacén ve los clientes, y el
vendedor ve el inventario. Es a propósito, para que un vendedor pueda checar si hay producto antes de
prometer una entrega, y para que quien atiende un reclamo pueda ver de qué lote salió. **Lo que cambia
entre roles no es lo que ves, sino lo que puedes escribir.**

### Los diez roles

| Rol | En qué módulos escribe | Qué tiene reservado |
|---|---|---|
| **Administrador** | Todo | Es el único que ve **Historial** y **Usuarios**, y el único que **autoriza compras** |
| **Ventas** | Prospectos (y los convierte), cuentas, oportunidades, cotizaciones, **pedidos**, casos, tareas | — |
| **Atención a clientes** | Prospectos, casos, tareas, **carga de correos** | — |
| **Calidad e inocuidad** | Casos, tareas | — |
| **Administración** | **Caja chica**, órdenes de compra, pedidos, casos, carga de correos y **generar los avisos** | **Caja chica** |
| **Almacén** | **Movimientos de inventario**, productos, bodegas y lotes, tareas | — |
| **Abastecimiento** | **Órdenes de compra**, inventario, tareas | — |
| **Recursos Humanos** | **Expedientes, contratos y puestos**, tareas | **Personal** |
| **Mantenimiento** | **Activos, planes y órdenes de trabajo**, tareas | — |
| **Solo lectura** | Nada, salvo silenciar y marcar leídos los avisos | — |

Todos los roles menos "solo lectura" pueden además **subir documentos** a los módulos en los que
escriben, y **registrar actividades**.

### Las cuatro secciones reservadas

| Sección | Quién entra |
|---|---|
| **Personal** (expedientes) | Recursos Humanos y el administrador |
| **Caja chica** | Administración y el administrador |
| **Historial** | Solo el administrador |
| **Usuarios** | Solo el administrador |

**Ojo con una confusión fácil:** la PARTE III de este manual agrupa **cinco** capítulos, pero solo estas
**cuatro** secciones están reservadas. El quinto, **Documentos**, lo ve todo el mundo — aunque cada quien
**solo los documentos de los módulos que puede leer**, así que un expediente de personal no se le aparece
a nadie fuera de RRHH.

Si intentas entrar a una sección que no te toca, verás un mensaje de error. Hoy está escrito en lenguaje
técnico y es confuso; ya está anotado para arreglarse.

---

## 5. El Tablero

**Para qué sirve:** es la pantalla de inicio. Un resumen de cómo va todo.

**Quién lo usa:** todos. **Casi el mismo para todos, pero no idéntico:** las tarjetas están
condicionadas por permiso, así que quien no ve Personal no ve su tarjeta, y quien no ve Caja chica
tampoco. Lo que sí es igual para todos es el bloque comercial y el de operación, y eso lo hace más denso
de lo necesario para algunos puestos. Está anotado para mejorarse.

**Qué mirar primero:** los **Avisos pendientes**, arriba. Es lo único de la pantalla que exige acción.

**[CAPTURA: el tablero completo, señalando el bloque de avisos pendientes]**

**Error de novato:** creer que el tablero se actualiza solo con todo. Las tarjetas sí se calculan al
momento, pero **los avisos no se generan solos**: alguien tiene que pulsar "Revisar ahora" en la
pantalla de Avisos. Es la cosa más importante de este manual, y está explicada en el capítulo 17.

---

# PARTE I · Lo comercial

## 6. Prospectos

**Para qué sirve:** guardar a **toda persona que pregunta**, aunque todavía no sea cliente.

**Quién escribe aquí:** Ventas y Atención a clientes.

Un **prospecto** es la *persona* que preguntó. No confundir con **Cliente potencial**, que es la
*empresa* que todavía no ha comprado. Persona y empresa son cosas distintas en el sistema.

### Tarea 1: dar de alta a alguien que acaba de preguntar

1. Menú → **Prospectos**.
2. Abajo, en **Nuevo prospecto**, llena el **nombre** y **al menos una forma de contactarlo: correo o
   teléfono**. En el formulario esos tres campos llevan asterisco, y debajo una nota lo aclara: el
   asterisco del correo y del teléfono significa **uno de los dos**, no los dos. Sin nombre no guarda, y
   sin correo ni teléfono tampoco. El resto se puede completar después.
3. Pulsa el botón de guardar.

**Y para poder calificarlo después necesitas el nombre de la empresa.** No hace falta al darlo de alta,
pero el sistema no te deja pasarlo a *calificado* sin ese dato, así que conviene preguntarlo desde la
primera llamada.

El sistema **te crea sola una tarea de primer contacto, con vencimiento a 4 horas hábiles**. Hábiles
quiere decir de lunes a viernes de 8 a 17, hora de Monterrey, y sin contar días festivos: si alguien
pregunta un viernes a las 16:30, la tarea vence el lunes, no el sábado.

**[CAPTURA: el formulario de Nuevo prospecto]**

### Tarea 2: registrar que ya le llamaste

1. **Menú → Prospectos**, y abre el prospecto desde la lista.
2. En la sección de actividades, registra la llamada con lo que quedó.
3. El prospecto pasa a **contactado**.

### Tarea 3: calificarlo (el paso que decide si se le va a vender)

Calificar es decir "este sí nos interesa y le podemos vender". Es el paso intermedio que separa una
pregunta cualquiera de una venta que se va a trabajar.

1. **Menú → Prospectos**, y abre el prospecto.
2. Pulsa el botón de cambiar estado y elige **calificado**.

**El sistema te va a exigir el nombre de la empresa.** Sin ese dato no deja calificar, porque una cuenta
sin nombre de empresa no sirve para nada después.

**Cómo se decide** —y esto es de negocio, no del sistema—: hoy el criterio de referencia es que el
volumen llegue a **500 kg**. PENDIENTE de confirmar si sigue vigente.

### La línea de estados de un prospecto

Como los pedidos y las órdenes de compra, un prospecto tiene su recorrido. Los cinco estados y lo que el
sistema permite:

| Estado | A dónde puede pasar |
|---|---|
| **nuevo** | contactado · calificado · descartado |
| **contactado** | calificado · descartado |
| **calificado** | descartado — o **convertido**, pero solo pulsando **Convertir**, no cambiando el estado |
| **descartado** | **nuevo** (se puede reabrir) |
| **convertido** | Ninguno: es el final del camino |

Dos cosas que conviene notar en esa tabla:

- **Se puede saltar "contactado"** e ir de nuevo directo a calificado. Si el cliente llegó recomendado y
  ya sabes que le vas a vender, no tienes que inventar una llamada.
- **Un descartado se puede reabrir.** Vuelve a *nuevo* y sigue teniendo su historial completo, incluido
  el motivo por el que se descartó la primera vez.

### Tarea 4: convertirlo en cliente

**Menú → Prospectos**, y abre el prospecto. Cuando ya está **calificado**, aparece el botón
**Convertir**. Con un solo clic el sistema crea tres cosas: la **Cuenta** (la empresa), el **Contacto**
(la persona dentro de esa empresa) y una **Oportunidad** (la venta que se va a perseguir).

**Solo Ventas puede convertir.** Atención a clientes da de alta el prospecto, pero el paso de convertir
lo hace Ventas.

**Qué no puede hacer aquí:** borrar un prospecto. Se **descarta** con un motivo, y queda guardado. Nada
se borra en este sistema, nunca.

**Cómo trata el sistema a alguien que ya estaba dado de alta.** Hay dos casos distintos y conviene no
confundirlos:

- **Mismo correo exacto:** **no se crea un segundo registro.** El sistema reconoce a la persona y le
  suma una actividad al prospecto que ya existía. Si das de alta a alguien y "no aparece en la lista
  como nuevo", esto es lo que pasó: búscalo por su correo y verás la nota agregada.
- **Mismo teléfono, o correo del mismo dominio que otro prospecto o cuenta:** sí se crea el registro,
  pero queda **marcado como posible duplicado** con el motivo. Ahí el sistema **no une nada solo**: hay
  que revisarlo y pulsar "Fusionar".

**Errores de novato:**
- Capturar solo el nombre y no entender por qué no guarda. Falta el correo o el teléfono.
- Volver a capturar a alguien con su mismo correo esperando un registro nuevo (ver arriba).
- Creer que "descartado" es "borrado". Sigue ahí, y se puede filtrar en la lista.

## 7. Cuentas y contactos

**Para qué sirve:** la ficha de cada empresa cliente y de las personas que trabajan en ella.

**Quién escribe aquí:** Ventas.

Cada cuenta tiene un **estado**: *Cliente potencial* (todavía no compra), *Cliente activo*, *Cliente
recurrente*. Lo importante es que **el sistema mueve ese estado solo**, en dos momentos: al **ganar** una
oportunidad y al **entregar** un pedido. Cualquiera de los dos pasa la cuenta de Cliente potencial a
Cliente activo sin que nadie lo teclee.

*Cliente recurrente* es un caso aparte y conviene saberlo: **solo lo asigna la sincronización con el ERP
simulado**, cuando la cuenta acumula dos pedidos **de los que vienen del ERP**. Los pedidos que capturas
tú en el sistema no cuentan para eso. Así que hoy una cuenta con cinco pedidos capturados aquí puede
seguir apareciendo como "Cliente activo". Cuando se conecte el ERP real, esa etiqueta empezará a
significar algo; mientras tanto, no te fíes de ella.

**Qué mirar:** al abrir una cuenta ves sus oportunidades, sus casos, sus correos y todo lo que se ha
platicado con ella. Es la pantalla que conviene tener abierta antes de llamarle a un cliente.

> **Lo que esa pantalla NO muestra todavía:** los pedidos que capturaste en el sistema. La tabla de
> "Pedidos" de la ficha trae los pedidos de referencia del ERP simulado, no los tuyos — la propia
> pantalla lo dice. Para ver los pedidos de un cliente, entra a **Pedidos** y fíltralos por cliente. El
> arreglo está anotado en el backlog y es chico: la función que los busca ya está escrita, solo falta
> conectarla.

**[CAPTURA: la vista de una cuenta con sus oportunidades y pedidos]**

## 8. Oportunidades

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

### Lo que decide qué etapas verás: el TIPO de oportunidad

Esto es lo más importante del capítulo y no es evidente en pantalla. **Cada oportunidad tiene un tipo, y
el tipo decide por cuáles etapas puede pasar.** No es que "saltarse etapas sea normal": es que **cada
tipo tiene su camino y el sistema no te deja salirte de él**.

| Tipo de oportunidad | Por dónde pasa | Qué NO puede hacer |
|---|---|---|
| **Estándar** (producto de catálogo) | Requerimiento → Cotización → Negociación → Ganada o Perdida | Las etapas de fórmula y de muestra **no existen** para ella: no hay manera de llegar a "Muestra enviada" |
| **Recompra** | El mismo camino que la estándar | Igual: nada de fórmula ni muestras |
| **Fórmula personalizada** | Las ocho, **en orden estricto**: Requerimiento → Desarrollo de fórmula → Muestra enviada → Muestra aprobada → Cotización → Negociación → Ganada o Perdida | **No puede saltar a Cotización.** Tiene que pasar por la fórmula y la muestra. De "Muestra enviada" sí puede regresar a "Desarrollo de fórmula" si el cliente pidió ajustes |

Desde cualquier etapa abierta se puede ir a **Perdida**, y eso **exige escribir el motivo**.

Dos reglas más que el sistema impone y conviene saber antes de que te detenga:

- **No se llega a Cotización ni a Ganada sin una cotización capturada.** Primero el documento, después
  la etapa.
- **Una oportunidad cerrada (ganada o perdida) ya no se mueve.** No hay manera de reabrirla.

Así que si eliges mal el tipo al crear la oportunidad, el camino que verás será el equivocado. Vale la
pena pensarlo un segundo al capturarla.

La pantalla es un **tablero de columnas** (una por etapa) con tarjetas. Ver dónde se acumulan las
tarjetas es el punto: si hay ocho en "Muestra enviada" y ninguna en "Muestra aprobada", **nadie está
dando seguimiento a las muestras**.

**[CAPTURA: el tablero de oportunidades por etapa]**

### Tarea común: hacer una cotización

1. **Menú → Oportunidades**, y abre la oportunidad.
2. Crea la cotización con sus renglones y precios.
3. Pulsa para generar el **PDF**, que trae su folio.
4. **Descárgalo y mándalo tú** por correo o WhatsApp. El sistema no lo envía.
5. Regresa y pulsa **Marcar enviada**. Eso le dice al sistema que ya salió, y te crea la tarea de
   seguimiento.

**Qué no puede hacer:** enviar la cotización. Y **no valida el precio**: puedes guardar un renglón en
cero y nadie te va a avisar. PENDIENTE: quién autoriza un descuento.

## 9. Pedidos

**Para qué sirve:** registrar lo que el cliente compró y **descontarlo del inventario** al entregarlo.

**Quién escribe aquí:** **Ventas y Administración**, y nadie más.

> **Ojo con esto, porque es contraintuitivo:** capturar, confirmar, **entregar**, cancelar y anotar el
> folio de la factura lo hacen Ventas o Administración. **Almacén no puede.** Ve el pedido y ve el
> descuento de inventario que produjo, pero los botones no le aparecen. Así que el paso de "entregar"
> lo registra en el sistema quien vende, no quien surte físicamente. PENDIENTE de decidir si Almacén
> debería poder hacerlo.

Un pedido pasa por cuatro estados: **borrador → confirmado → entregado**, o **cancelado**.

### Tarea 1: capturar el pedido

Menú → **Pedidos** → nuevo. Se captura la cuenta, la bodega de donde saldrá, la fecha prometida y los
renglones **en kilos**. **La fecha prometida es obligatoria** y el pedido necesita al menos un renglón.
El sistema acepta fechas pasadas sin avisar, así que revísala.

### Tarea 2: confirmar

**Menú → Pedidos**, abre el pedido y pulsa **Confirmar**. El sistema revisa que haya existencia.

> **OJO, esto es importante:** confirmar **revisa pero no aparta**. El producto sigue disponible para
> otro pedido. Si dos vendedores confirman pedidos sobre los mismos kilos, los dos pasan, y el conflicto
> aparece hasta que alguien intente entregar. PENDIENTE de decidir; está anotado como riesgo.

### Tarea 3: entregar

**Menú → Pedidos**, abre el pedido confirmado y pulsa **Entregar**. Aquí pasan tres cosas de golpe:

1. El sistema **descuenta el inventario**, y **sale primero el lote que caduca antes**. Esa decisión la
   toma el sistema; nadie tiene que elegir el lote a mano.
2. Es **todo o nada**: si falta producto en un solo renglón, no se descuenta ninguno y el pedido se
   queda como estaba. No existe la entrega parcial.
3. Si era el primer pedido de esa cuenta, pasa a **Cliente activo**.

**[CAPTURA: un pedido entregado mostrando los movimientos de inventario que generó]**

### Tarea 4: anotar el folio de la factura

**Menú → Pedidos**, abre el pedido. Cuando CONTPAQi ya emitió la factura, se captura ahí **solo el
folio**. El sistema no factura ni
verifica el folio: lo guarda como referencia.

**Solo se puede capturar en un pedido confirmado o entregado.** En un borrador el sistema te pide
confirmarlo primero, y en uno cancelado no lo acepta.

**Qué no puede hacer Pedidos:** facturar, cobrar, apartar producto, entregar a medias, registrar una
devolución, ni guardar dirección de entrega o guía del transportista.

**Errores de novato:**
- Creer que confirmar aparta el producto. No lo aparta.
- Intentar entregar un borrador. Hay que confirmarlo primero.
- Buscar cómo deshacer una entrega. **No se puede**: "entregado" es final. Un error se corrige con un
  ajuste de inventario, y eso lo hace Almacén.

## 10. Correos

**Para qué sirve:** leer el buzón, **clasificar solo** cada mensaje y sugerir qué hacer con él.

**Quién escribe aquí:** **cargar** correos lo pueden hacer Atención a clientes y Administración.
**Revisar y aplicar** sugerencias lo pueden hacer además **Ventas y Calidad** (los cuatro tienen
`email:review`).

El sistema lee y propone; **nunca actúa solo**. No responde, no borra, no archiva y no mueve nada en el
buzón. Cada sugerencia se aplica con un clic humano.

**Menú → Correos** para todo lo de este capítulo.

### Las dos formas de meter correos

- **Cargar correos de ejemplo:** trae un buzón de demostración que viene incluido. Es **solo para
  practicar**; no toca ningún buzón real.
- **Subir un archivo `.eml`:** un `.eml` es lo que se genera cuando guardas un correo como archivo desde
  Outlook o Gmail. Sirve para probar el clasificador con un correo real sin conectar el buzón.

### La bandeja "Needs Review"

Cuando el sistema no está seguro de cómo clasificar un correo, **no adivina**: lo manda a esa bandeja
para que una persona decida. Que un correo caiga ahí no es una falla, es el diseño.

**Son dos clics, no uno.** Primero **confirmas o corriges** la categoría, y después **aplicas** la
sugerencia. Si intentas aplicar sin haber confirmado, el sistema te detiene con el mensaje "primero
confirma o corrige la categoría". No es un error: es para que nadie aplique a ciegas lo que el sistema
mismo marcó como dudoso.

**[CAPTURA: un correo clasificado, mostrando las entidades detectadas y el botón Aplicar]**

**Errores de novato:**
- Pensar que "Cargar correos de ejemplo" va a traer el correo real de la empresa. No: son de práctica.
- Esperar que el sistema conteste. No contesta. PENDIENTE: quién responde y con qué.

## 11. Casos

**Para qué sirve:** llevar un problema del cliente hasta resolverlo. Sobre todo **reclamaciones de
calidad**.

**Quién lo crea:** **nadie, a mano.** Un caso nace **al aplicar la sugerencia de un correo
clasificado**. No hay ningún formulario de alta en el sistema.

**Quién trabaja un caso ya existente:** Calidad, Atención a clientes, Ventas y Administración. Esos
cuatro pueden avanzar su estado, registrar actividades y subir evidencia.

> **La consecuencia práctica, y es grande: una reclamación que llega por teléfono no se puede registrar
> hoy.** El único camino es que alguien se mande a sí mismo un correo con el asunto del reclamo y lo
> clasifique, lo cual es un truco, no un procedimiento. Está anotado en el backlog como UI-6, y es el
> hueco más serio del módulo para una empacadora de alimentos, donde el caso es el vehículo de las
> reclamaciones de calidad.

Lo específico de este módulo: una reclamación de calidad **necesita el número de lote** para poder
resolverse.

**Qué tan lejos llega hoy el rastreo, sin adornos.** Los datos están completos: cada movimiento de
salida guarda a qué pedido salió cada kilo, y cada lote tiene su código. **Pero la pantalla todavía no
lo aprovecha:** el historial de movimientos se filtra solo por producto y por bodega — **no por lote** —
y la columna de referencia imprime la palabra "pedido" sin el folio ni el nombre del cliente.

En la práctica: para saber a qué clientes les llegó un lote, hoy hay que **abrir los pedidos uno por
uno**. La información existe y es confiable; lo que falta es la vista que la junte. Es lo primero de
`RN-5` en el backlog y es un arreglo chico.

**Qué no puede hacer:** bloquear un lote sospechoso para que no se venda (no existe), impedir la venta
de un lote caducado (no la impide), registrar la devolución del producto, ni abrir un caso desde una
pantalla. PENDIENTES los cuatro, agrupados como **RN-5 · no se puede hacer un retiro de producto**.

**Error de novato:** cerrar un caso sin anotar el lote. El sistema lo exige para las reclamaciones de
calidad, y con razón: sin lote no hay rastreo posible ni después.

---

# PARTE II · La operación

## 12. Productos, bodegas y lotes — el capítulo que va antes de todo lo demás

**Para qué sirve:** definir **sobre qué** se lleva el inventario. Sin esto capturado, los movimientos no
tienen dónde caer y **tres campos del producto que sostienen las alertas quedan vacíos**.

**Quién escribe aquí:** Almacén, Abastecimiento y el administrador.

Este capítulo va primero porque es la configuración que hace que lo demás sirva. Es trabajo de una sola
vez, y es el que nadie quiere hacer.

### Por qué importa tanto: tres campos del producto sostienen las alertas

| Campo del producto | Qué se cae si está vacío |
|---|---|
| **Mínimo en kilos** | **La alerta de existencia baja nunca se dispara.** El sistema no tiene con qué comparar, así que el producto se puede acabar en silencio |
| **Vida útil en días** | Si al recibir mercancía nadie captura la caducidad a mano, el sistema **la calcula sumando estos días**. Sin el dato y sin captura manual, el lote queda **sin caducidad** y **la alerta de lote por caducar nunca lo ve** |
| **Kilos por unidad** | Es lo que convierte sacos y cajas a kilos. Si está mal, **todas las cantidades quedan mal**: la existencia, lo que se descuenta en una entrega y el disparo del mínimo |

Dicho de otro modo: **el sistema no puede avisar de lo que no sabe medir.**

### Tarea 1: dar de alta un producto

1. **Menú → Inventario → Productos.**
2. Captura la **clave** (única, se guarda en mayúsculas), el **nombre**, la categoría y las palabras
   clave que ayuden a encontrarlo.
3. Elige la **unidad** en la que lo manejas —kilogramos, saco, caja o tarima— y **cuántos kilos tiene una
   unidad**. Si trabajas en kilos, es 1.
4. Captura el **mínimo en kilos** y la **vida útil en días**. Para el sistema son opcionales; para que te
   avise, son indispensables. Vuelve a leer la tabla de arriba antes de dejarlos en blanco.

**[CAPTURA: el formulario de alta de producto, señalando mínimo, vida útil y kilos por unidad]**

### Tarea 2: corregir un producto ya dado de alta

1. **Menú → Inventario → Productos**, y abre el que quieras cambiar.
2. Puedes cambiar cinco cosas: **unidad, kilos por unidad, empaque, mínimo en kilos y vida útil**.

> **Lo que NO se puede cambiar:** la **clave**, el **nombre**, la **categoría** ni las palabras clave. Si
> capturaste mal el nombre de un producto, **hoy no hay forma de corregirlo desde la pantalla**. No es que
> te falte permiso: el sistema no lo permite para nadie. Está anotado en el backlog.

### Tarea 3: dar de alta una bodega

1. **Menú → Inventario → Bodegas.**
2. Captura la **clave** (se guarda en mayúsculas), el **nombre** y la dirección.

> **Las bodegas tampoco se pueden editar después.** Si algo quedó mal, se da de alta otra y la primera se
> deja de usar. Anotado también.

### Tarea 4: dar de alta un lote a mano

1. **Menú → Inventario → Lotes.**
2. Elige el producto, captura el **código de lote** y, si la sabes, la **caducidad**.

**Normalmente no vas a usar esta pantalla**, porque los lotes se crean solos al recibir una orden de
compra. Sirve para el arranque —meter al sistema lo que ya está en la bodega— y para casos sueltos.

**Qué no puede hacer este módulo:** editar un producto más allá de esos cinco campos, editar bodegas,
editar o borrar lotes, dar de baja un producto, y no guarda ningún costo ni precio de venta. Los precios
de compra viven dentro de las órdenes; **no existe una lista de precios de venta**.

**Errores de novato:**
- Dar de alta los productos sin mínimo ni vida útil "para avanzar rápido", y después esperar que el
  sistema avise. No va a avisar.
- Poner mal los kilos por unidad. Un saco declarado de 25 kg que en realidad trae 50 hace que **todo el
  inventario mienta**, y el sistema no tiene forma de notarlo.
- Escribir mal el nombre de un producto. No se puede corregir.

---

## 13. Inventario

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

**Menú → Inventario → Movimientos.** Se usa cuando algo entró o salió sin pasar por un pedido ni por una
compra. Elige el tipo, el producto, la bodega, la cantidad y **el lote**.

**No tienes que convertir a kilos tú.** El formulario tiene un campo de **unidad**: puedes capturar en
kilogramos, **sacos, cajas o tarimas**, y el sistema hace la conversión con los kilos por unidad que
tenga registrado el producto. Ojo: eso vale para el inventario. **Las órdenes de compra sí se capturan
solo en kilos.**

> **Captura siempre el lote.** El sistema te deja guardar una salida sin lote, y cuando lo haces la
> cuenta total queda bien pero **el lote sigue diciendo que tiene lo que ya salió**. Se pierde el
> rastreo, que es justo lo que se necesita cuando hay una reclamación. Ya está anotado para arreglarse;
> mientras tanto, es disciplina de captura.

### Tarea 3: hacer un ajuste

**Menú → Inventario → Movimientos**, igual que un movimiento normal pero con tipo **Ajuste**, y el
sistema **te obliga a escribir el motivo**. Escribe
algo que se entienda en seis meses: "conteo físico del 15 de marzo, faltaban 3 kg", no "corrección".

**Qué no puede hacer Inventario:** no valora el inventario en pesos, no registra conteos físicos como
tal (solo el ajuste que resulta), no impide vender un lote caducado, y **ningún movimiento se puede
borrar ni editar**. Para corregir, otro movimiento.

**Errores de novato:**
- Buscar dónde "poner" la existencia correcta. No se pone: se captura el movimiento que falta.
- Capturar una salida sin lote (ver el aviso de arriba).
- No poner motivo en un ajuste y no entender por qué no guarda.

## 14. Abastecimiento

**Para qué sirve:** las órdenes de compra a proveedores, y **meter la mercancía al inventario cuando
llega**.

**Quién escribe aquí:** Abastecimiento y Administración. **Quien autoriza es solo el administrador.**

> **Lo primero que hay que saber de este módulo no es una pantalla, es un hueco.** El aviso de
> "existencia bajo el mínimo" —el que dispara una compra— **está dirigido a Almacén, no a
> Abastecimiento**. Quien tiene que comprar **no recibe la señal de que hay que comprar**. Hoy se
> entera porque revisa el inventario por su cuenta o porque alguien de bodega se lo dice de viva voz.
> El sistema no tiene mensajes entre áreas. PENDIENTE de resolver, y está en el backlog.

Una orden pasa por: **borrador → por autorizar → autorizada → recibida**, o **cancelada**.

### Tarea 1: crear la orden

Menú → **Abastecimiento** → Nueva orden de compra. Se elige el proveedor y se capturan los renglones en
kilos con su costo, **hasta cinco renglones**. Queda en **borrador**.

> **"Borrador" no quiere decir editable.** Significa que todavía no se envió. **No hay pantalla para
> corregir una orden ni sus renglones**: si algo salió mal, se cancela con su motivo y se captura otra.
> Revisa bien antes de guardar.

**Dónde está el historial de precios:** no en la ficha del proveedor, sino **dentro de la orden de
compra**, y es **por producto**, no por proveedor. Al abrir una orden verás, para cada renglón, a qué
precio te vendió ese mismo producto cada proveedor la última vez y su promedio por kilo. Sirve para
saber si lo que te están cotizando hoy es caro — pero lo ves al revisar la orden, no antes de crearla.

### Tarea 2: enviarla

**Menú → Abastecimiento**, abre la orden en borrador y pulsa **Enviar**. Aquí el sistema decide solo:

- Si el total **no pasa de $20,000**, queda **autorizada** de una vez.
- Si **pasa de $20,000**, queda **por autorizar** y hay que esperar al administrador.

**Ese monto de $20,000 es provisional y se puede cambiar sin tocar el código**: es un ajuste del
servidor (la variable `CRM_PO_AUTH_THRESHOLD_MXN`), así que lo mueve quien instala el sistema. Lo que
**no** existe es una pantalla para cambiarlo: nadie lo ajusta desde el navegador. PENDIENTE de confirmar
con La Huerta si 20,000 es la cifra correcta.

**Autorizar es exclusivo del administrador, y es a propósito:** quien crea la orden no debe poder
aprobarla. Si Abastecimiento tuviera esa llave, aprobaría sus propias compras.

**[CAPTURA: una orden en estado "por autorizar", con el botón de autorizar visible solo para el administrador]**

### Tarea 3: recibir la mercancía

**Menú → Abastecimiento**, abre la orden autorizada. Cuando llega el producto, pulsa **Recibir** y
captura, renglón por renglón: los kilos que de verdad
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
- Buscar cómo cancelar una orden **ya recibida**. No se puede, en absoluto: el sistema solo cancela
  órdenes en borrador, por autorizar o autorizadas. El caso que sí ocurre es la orden **recibida a
  medias**, que sigue estando "autorizada" y por tanto **sí se puede cancelar** — y cuando se cancela,
  **los kilos que ya entraron se quedan en el inventario**. Cancelar nunca deshace una entrada.

## 15. Mantenimiento

**Para qué sirve:** que no se te pase el servicio de un camión ni la verificación de un equipo.

**Quién escribe aquí:** Mantenimiento.

Tres conceptos: el **activo** (el camión, el clima, el equipo), el **plan** (cada cuándo le toca) y la
**orden de trabajo** (el servicio concreto que se hizo o se va a hacer).

### Lo que hace especial a este módulo

Un plan se puede medir por **días, por kilómetros y por horas al mismo tiempo**, y **vence lo que ocurra
primero**. Un camión puede tener "cada 6 meses o cada 10,000 km, lo que llegue antes".

### Tarea 1: capturar el kilometraje

**Menú → Mantenimiento**, abre el activo y captura la lectura del odómetro.

> **Esto es lo más importante del módulo.** La lectura **solo puede subir**: si capturas un número menor
> el sistema lo rechaza, para protegerte de un error de dedo. Y tiene una consecuencia: **si nadie
> captura el kilometraje, el plan por kilómetros nunca avisa.** El plan por días sí avisa solo, porque
> el calendario avanza sin que nadie lo teclee. PENDIENTE: quién lo captura y cada cuándo.

### Tarea 2: abrir una orden de trabajo

**Menú → Mantenimiento → Órdenes.** Cuando toca servicio, o cuando algo se rompió, abre la orden: si es
**preventivo** (lo programado) o **correctivo** (se falló), y si lo hace el taller **interno** o un
proveedor **externo**. Si es externo, el nombre del proveedor es obligatorio.

### Tarea 3: cerrar la orden

**Menú → Mantenimiento → Órdenes**, abre la orden. Al terminar el servicio, captura el costo, la fecha,
el kilometraje y las notas. El sistema **reprograma el plan
desde lo que realmente se hizo**, no desde lo que estaba programado. Así el plan no se desfasa con los
meses.

**[CAPTURA: la ficha de un camión con su plan por kilometraje y su historial de órdenes]**

**Qué no puede hacer:** crear la orden sola cuando un plan vence (avisa, pero alguien decide),
descontar refacciones del inventario, desglosar mano de obra y piezas, y **hoy no se puede cancelar una
orden desde la pantalla**, ni marcarla "en proceso", **ni desactivar un plan** que ya no aplique. Las
tres funciones existen en el código sin puerta de entrada, y están anotadas.

## 16. Tareas

**Para qué sirve:** que no se te olvide lo que quedaste de hacer, y poder pedirle algo a otra área.

**Quién escribe aquí:** todos los roles menos "solo lectura".

Una tarea tiene responsable, fecha de vencimiento y estado.

> **A quién puedes asignarle una tarea hoy:** el formulario ofrece **solo cuatro áreas** — Ventas,
> Atención a clientes, Calidad y Administración — y **no permite elegir a una persona concreta**. Es
> decir: **no puedes pedirle nada por el sistema a Almacén, Abastecimiento, Mantenimiento ni RRHH.** Las
> tareas que el sistema crea solo sí llevan persona asignada; las que capturas a mano, no. Para pedirle
> algo a esas áreas hay que hablarles.

**Lo que conviene saber:** el sistema **crea tareas solo** en tres momentos, sin que nadie las teclee:

1. Al dar de alta un prospecto → tarea de primer contacto, a 4 horas hábiles.
2. Al ganar una oportunidad → tarea para Administración.
3. Al marcar una cotización como enviada → tarea de seguimiento.

Las fechas de vencimiento respetan **horario hábil**: lunes a viernes de 8 a 17, hora de Monterrey, sin
festivos. Una tarea creada el viernes a las 16:30 con 4 horas de plazo vence el lunes.

Cuando una tarea se pasa de su fecha, genera un **aviso** para quien la tenga asignada — siempre y cuando
alguien haya pulsado "Revisar ahora" (ver el capítulo siguiente).

### Tarea 1: ver qué te toca hoy

1. **Menú → Tareas.**
2. La lista abre en **pendientes**. Filtra por **urgencia** si quieres ver primero las altas.
3. Verás las tuyas y las de tu área, porque una tarea puede estar dirigida a un rol completo.

### Tarea 2: crear una tarea

1. **Menú → Tareas**, y usa el formulario de abajo.
2. Captura el título, elige el **área** responsable y la fecha de vencimiento.
3. Recuerda el límite de arriba: **solo cuatro áreas** en la lista, y no se puede elegir a una persona.

### Tarea 3: cerrar una tarea

1. **Menú → Tareas**, y marca la tarea como atendida.
2. **Antes de cerrarla, registra en la cuenta o el prospecto lo que hiciste.** La tarea desaparece de la
   lista; la actividad es lo que le va a servir a quien atienda a ese cliente el mes que viene.

**[CAPTURA: la lista de tareas filtrada por pendientes, con una vencida marcada]**

**Qué no puede hacer:** no manda recordatorios por correo, y no hay subtareas ni dependencias entre
tareas.

**Error de novato:** cerrar una tarea sin registrar lo que se hizo. La tarea desaparece de la lista, pero
la actividad —la llamada, el correo, el acuerdo— es lo que le sirve al que atienda a ese cliente después.
Regístrala en la cuenta o el prospecto.

## 17. Avisos — el capítulo que hay que leer completo

**Para qué sirve:** que el sistema te diga lo que se está por vencer antes de que te cueste dinero.

**Quién lo ve:** todos, cada uno los de su área.

### Las seis cosas que vigila

| Aviso | Cuándo aparece | A quién |
|---|---|---|
| Contrato por vencer | 60 días antes | Recursos Humanos |
| Documento por vencer | 30 días antes | Mantenimiento si es de un activo, RRHH si es de un empleado, Administración si es de una caja — **y Administración también para todo lo demás** |
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

> **Y hay un detalle incómodo en esa rutina:** quien pulsa el botón **no ve la mayoría de los avisos que
> acaba de generar.** Los avisos se muestran al área destinataria, y los de lote por caducar, existencia
> baja y mantenimiento van a Almacén y a Mantenimiento. Administración pulsa, se generan, y en su propia
> pantalla no aparece casi nada. No está roto: es el filtro por área haciendo su trabajo. Solo el
> administrador ve todos. Si alguien va a hacer esta rutina a diario, conviene que sea el administrador,
> o que después pregunte si a las otras áreas les llegó algo.

**[CAPTURA: la pantalla de avisos con el botón "Revisar ahora" señalado]**

### Cómo apagar un aviso

- **Marcar leído:** lo quitas de pendientes.
- **Silenciar:** hay **exactamente dos opciones, 30 días o sin fecha** (o sea, para siempre). No se puede
  poner otro plazo. Sirve para el lote que ya sabes que vas a rematar y no quieres que te lo recuerden
  cada semana.

**Cualquier rol puede silenciar y marcar leído, incluso el de solo lectura.** Está hecho así a propósito
—silenciar es decisión del área— pero ya se decidió que debe pedir permiso de escritura del módulo;
todavía no está cambiado.

Pulsar "Revisar ahora" cinco veces el mismo día **no genera cinco avisos iguales**: el sistema sabe que
ya avisó de eso en este periodo.

**Error de novato:** silenciar un aviso para siempre por quitárselo de encima. Silenciar el lote de un
producto apaga ese recordatorio de forma permanente. Usa días.

---

# PARTE III · Lo reservado

## 18. Personal

**Para qué sirve:** el expediente de cada empleado y el control de sus contratos.

**Quién entra:** **solo Recursos Humanos y el administrador.** Cada consulta queda registrada.

Guarda: número de empleado, nombre, área, puesto, fecha de ingreso, teléfono, correo, notas y los
documentos escaneados (contrato, identificación, certificados).

El **puesto** describe funciones y requisitos, uno por renglón. A pesar de lo que decía un documento
anterior, **no es un sistema de puntos ni una valuación**: son viñetas. **Necesita al menos una función**
para guardarse, el título no se repite, y una vez creado **no hay pantalla para editarlo** — la función
existe en el código pero no tiene puerta de entrada. Está anotado en el backlog.

### Las tres tareas

1. **Dar de alta el expediente:** **Menú → Personal**, con el número de empleado (único) y el nombre.
2. **Registrar el contrato**: temporal o indeterminado, con sus fechas. **Solo puede haber un contrato
   vigente por persona.** Un contrato **temporal exige fecha de término, y posterior a la de inicio**. Y
   a alguien **dado de baja ya no se le puede registrar un contrato nuevo**. Sube el PDF escaneado.
3. **Renovar o terminar** cuando el aviso llegue a 60 días. Al renovar, el anterior queda marcado como
   renovado y nace uno nuevo: la cadena completa queda guardada.

Un contrato **indeterminado no vence y por tanto nunca avisa**. Solo los temporales avisan.

Al dar de baja a alguien se exige motivo, se cierran sus contratos y **nada se borra**.

**[CAPTURA: un expediente con su contrato y la alerta de vencimiento]**

**Qué no puede hacer:** calcular nómina (no guarda sueldo), registrar asistencia, vacaciones o
incidencias, emitir contratos en PDF, ni conectarse con IMSS o SAT.

> **Antes de cargar expedientes reales hace falta el aviso de privacidad firmado.** No es un detalle
> técnico: es un requisito legal. Mientras no exista, el módulo debe usarse solo con datos de prueba.

## 19. Caja chica

**Para qué sirve:** llevar el efectivo con su comprobante y entregarle al contador un archivo limpio.

**Quién entra:** **solo Administración y el administrador.**

**El saldo** se calcula así: monto del fondo, más las reposiciones, menos los gastos. No hay un número
guardado: se recalcula cada vez.

### Las tres tareas

1. **Registrar un gasto:** **Menú → Caja chica**, abre el fondo y captura monto, categoría, descripción
   y **el comprobante, que es obligatorio**. Sin
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

## 20. Documentos

**Para qué sirve:** ver de un tirón **todo lo que está por vencerse**: pólizas, seguros,
verificaciones, contratos escaneados.

**Quién lo ve:** todos, **pero cada quien solo los documentos de los módulos que puede leer**. Un
documento de un expediente lo ven RRHH y el administrador; un comprobante de caja, Administración y el
administrador.

**Quién puede subir:** solo quien **escribe** en ese módulo. RRHH sube al expediente de un empleado,
Administración al de una caja, Mantenimiento al de un camión. Si intentas adjuntar algo a un módulo que
no te toca, el sistema lo rechaza — y es a propósito: un documento en el expediente de alguien se lee
como si lo hubiera puesto su área.

**Y solo se puede subir desde cinco pantallas**, las de: el expediente de un empleado, el detalle de una
caja chica, la ficha de un activo, el detalle de una orden de compra y el detalle de un pedido. No hay
un botón general de "subir documento" en la pestaña Documentos: esa pestaña solo sirve para ver
vencimientos.

El sistema **guarda los archivos tal cual y nunca los lee**. No hay lectura automática de texto: si un
documento tiene vencimiento, alguien lo captura y entonces el sistema avisa.

**Qué no puede hacer:** borrar un documento (para no perder evidencia), editarlo después de subirlo, ni
leer su contenido.

## 21. Historial

**Para qué sirve:** saber **quién hizo qué, cuándo y desde dónde**. Es la razón de ser del sistema para
una empresa que necesita auditar.

**Quién lo ve:** **solo el administrador.**

Se registra **cada acción de cada usuario**: no solo los cambios, también las consultas, las descargas,
los inicios de sesión y los intentos rechazados. Y nadie, ni el administrador, puede editar o borrar un
renglón del historial: el sistema no tiene ninguna función para hacerlo.

**Con cuatro excepciones deliberadas**, todas rutas técnicas que no son acciones de nadie: la pantalla de
acceso, la de salida, el icono del sitio, la verificación de salud del servidor, y el contador de avisos
que el navegador consulta en cada carga de página. Esta última está documentada como decisión D-55,
porque registrarla llenaría la bitácora de ruido.

Los tres filtros que parecen lo mismo y no lo son:

- **Tipo de evento:** la naturaleza de lo ocurrido (cambios de datos, consultas, seguridad, sistema).
- **Sobre qué registro:** en qué vive el evento (un prospecto, una cuenta, un pedido, una pantalla).
- **El nombre técnico del evento:** búsqueda libre sobre el identificador interno. Es para quien audita
  el código, no para el uso diario.

La columna **Detalle** es lo importante: dice qué cambió, en la forma `etapa: nuevo → contactado`.

El **usuario** de cada renglón se guarda como el correo **congelado al momento del evento**: si alguien
cambia de nombre o de área, su historial anterior no se reescribe.

**[CAPTURA: el historial filtrado por usuario, señalando la columna Detalle]**

## 22. Usuarios

**Para qué sirve:** dar de alta y de baja personas, cambiarles el área y la contraseña.

**Quién entra:** **solo el administrador.** Todo cambio queda en el historial.

Dos reglas que el sistema impone:

- **La contraseña debe tener al menos 10 caracteres**, tanto la temporal que le pones a alguien al darlo
  de alta como la que se cambie después.
- **No se puede desactivar al último administrador activo**, ni quitarle el rol. Es una protección
  contra quedarse fuera del sistema sin nadie que pueda volver a entrar.

### Tarea 1: dar de alta a una persona

1. **Menú → Usuarios.**
2. Captura su nombre, su correo (será su usuario) y elige su **rol**. Si dudas cuál, revisa la tabla de
   los diez roles del capítulo 4.
3. Ponle una **contraseña temporal de al menos 10 caracteres** y pídele que la cambie al entrar.

### Tarea 2: cambiar a alguien de área

1. **Menú → Usuarios**, y cámbiale el rol.
2. **Su historial anterior no se reescribe.** Lo que hizo cuando era de Ventas sigue registrado como lo
   que hizo entonces; el sistema guarda el correo congelado al momento de cada evento.

### Tarea 3: dar de baja a alguien que ya no trabaja aquí

1. **Menú → Usuarios**, y **desactívalo**. No lo borres: no hay botón de borrar, y es a propósito.
2. Desactivar le quita el acceso y **conserva intacto todo su historial**.

> **Hazlo el mismo día que la persona sale.** Una cuenta activa de alguien que ya no trabaja aquí es la
> única forma de que el historial mienta sin que nadie se dé cuenta.

---

# PARTE IV · Cuidar el sistema

## 23. Respaldos, contraseñas y qué hacer si algo se rompe

Este capítulo no es de un módulo: es de cuidar el sistema. Es corto y conviene que lo lean todos.

### El respaldo: quién, cómo y cada cuándo

Toda la información del sistema vive en **un solo archivo**: `data/crm.db`. Eso tiene una ventaja y un
riesgo. La ventaja es que respaldar es copiar un archivo. El riesgo es que si ese archivo se pierde, se
pierde todo: clientes, existencias, expedientes, caja y el historial completo.

**El sistema trae un comando para respaldar**, y hace la copia bien incluso con gente usando el sistema
en ese momento:

```
python scripts/backup_db.py
```

Deja el archivo en la carpeta `backups/`, con la fecha y la hora en el nombre — por ejemplo
`crm-20260926-1830.db`. Nada se sobrescribe: cada respaldo es uno nuevo.

**Lo que el sistema NO hace, y hay que resolver fuera de él:**

- **No respalda solo.** No hay nada programado: alguien tiene que correr el comando, o programarlo en el
  servidor. PENDIENTE.
- **No saca la copia de la computadora.** La carpeta `backups/` está en el mismo equipo que la base. Si
  se moja, se roba o se quema esa máquina, se van las dos cosas juntas. **Un respaldo que vive en el
  mismo lugar que el original no es un respaldo.** Hay que copiarlo a otro lado: disco externo, otro
  equipo o la nube.
- **No incluye los documentos escaneados.** Los archivos adjuntos —identificaciones, contratos,
  comprobantes de caja, pólizas— viven en la carpeta `data/uploads/`, **no dentro de la base**. Hay que
  respaldar esa carpeta también, o los registros van a apuntar a archivos que ya no existen.

**Antes de cualquier cosa grande** —cargar datos reales, una actualización, mover el sistema de máquina—
saca un respaldo a mano. Cuesta un minuto.

### Qué hacer si algo se rompe

1. **No borres nada, y no vuelvas a capturar "para arreglarlo".** En este sistema nada se corrige
   borrando, y duplicar registros hace más difícil entender qué pasó.
2. **Anota qué estabas haciendo, en qué pantalla y qué decía el mensaje.** Con eso y el historial se
   reconstruye lo que pasó; sin eso, no.
3. **Avisa a quien administra el sistema.** Si dejó de responder, lo primero que va a preguntar es cuál
   es el respaldo más reciente.

### Las tres reglas de tu cuenta

1. **No compartas tu contraseña ni uses la de otro.** Ya está en el capítulo 4, y se repite aquí porque
   es la que sostiene todo lo demás: el historial es confiable únicamente si cada sesión es de una sola
   persona.
2. **Diez caracteres como mínimo**, y cámbiala la primera vez que entres si te la dieron temporal.
3. **Cuando alguien deja de trabajar aquí, su cuenta se desactiva el mismo día.** Le toca al
   administrador, y es la única forma de que el historial no empiece a mentir.

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

# Las preguntas abiertas viven en otro documento

Las cosas que **no se pueden contestar leyendo el sistema** —y que cambian decisiones— están en
**`docs/13_GUIA_DE_JUNTA.md`**, agrupadas por persona y en el orden en que conviene preguntarlas: una
sesión por área, con el diagrama de esa persona enfrente.

Se sacaron de este manual a propósito. El manual es para quien va a **usar** el sistema, y conserva cada
**PENDIENTE** en el capítulo donde importa. La lista completa es para quien va a **decidir**, y esa
conversación se tiene una vez, no se consulta a diario.
