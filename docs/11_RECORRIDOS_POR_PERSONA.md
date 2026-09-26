# 11 · Los recorridos, persona por persona

Septiembre 2026. Informe de la Fase 3. Acompaña a los diagramas `14` a `24` de `docs/diagrams/`.

Etiquetas de evidencia: **VERIFICADO** = comprobado en el código o corriendo el sistema ·
**INFERIDO** = razonamiento que puede estar equivocado · **PENDIENTE** = falta preguntárselo al cliente.

## Advertencia que hay que leer antes de usar estos diagramas

**El orden del día de cada persona es INFERIDO, no verificado.** Lo que sí está verificado es *qué
puede hacer* cada rol: eso se lee en la matriz de permisos. Lo que **deduje** es el orden en que lo
hace, qué mira primero al entrar y cómo le pasa el trabajo al siguiente. Nunca he visto trabajar a
nadie de La Huerta.

Estos once diagramas son, entonces, un **borrador para que el cliente lo corrija**, no un retrato.
Sirven mejor si se los enseñas a cada persona y le preguntas "¿así es tu día?". Lo más probable es que
cambien, y ese es el punto.

Lo mismo aplica a **la frase de cada rol**: está escrita en primera persona para que suene a esa
persona, pero **la escribí yo**, no ella. Cada diagrama lo dice al lado de la frase. Confírmalas o
cámbialas con las suyas.

## Los archivos y su frase

| Archivo | Rol | Frase (INFERIDA) |
|---|---|---|
| `14_uso_administrador.mmd` | Administrador | "Es donde veo si el negocio va bien y donde autorizo lo que cuesta dinero" |
| `15_uso_ventas.mmd` | Ventas | "Es mi libreta de clientes: me dice a quién le debo una respuesta hoy y si hay producto para prometer una entrega" |
| `16_uso_almacen.mmd` | Almacén | "Es el control de lo que hay en bodega: me dice qué se va a caducar y qué se está acabando, y cuando surto un pedido lo baja solo" |
| `17_uso_abastecimiento.mmd` | Abastecimiento | "Es mi lista de qué falta y qué ya viene: qué se está acabando y en qué órdenes estoy esperando mercancía" |
| `18_uso_rrhh.mmd` | Recursos Humanos | "Es donde tengo los expedientes y lo que me recuerda que un contrato se vence antes de que se me pase" |
| `19_uso_administracion.mmd` | Administración | "Es donde llevo los gastos con su comprobante y donde veo qué se factura y qué falta cobrar" |
| `20_uso_mantenimiento.mmd` | Mantenimiento | "Es lo que me recuerda cuándo le toca servicio a cada camión, y donde anoto lo que se le hizo" |
| `21_uso_lectura.mmd` | Solo lectura | "Es una ventana al negocio: quiero ver cómo va sin preguntarle a nadie y sin riesgo de desconfigurar algo" |

Más `23_uso_atencion.mmd` y `24_uso_calidad.mmd` (ver el final de este documento) y
`22_uso_general.mmd`, que muestra cómo se entrelazan los recorridos.

---

## Lo que se ve al poner los diez recorridos juntos

### 1. Cada rol tiene exactamente una cosa que solo él puede hacer

Es el hallazgo más útil de la fase, y VERIFICADO en la matriz de permisos:

| Rol | Su llave exclusiva |
|---|---|
| Administrador | **Autorizar una compra** sobre el umbral, ver el historial, administrar usuarios |
| Ventas | **Convertir** un prospecto en cuenta, y cotizar |
| Almacén | **Mover existencias** (junto con Abastecimiento) |
| Abastecimiento | **Crear órdenes de compra** (junto con Administración) |
| RRHH | **Ver y escribir expedientes** |
| Administración | **Caja chica**, y generar los avisos |
| Mantenimiento | **Activos, planes y órdenes de trabajo** |
| Atención a clientes | **Cargar correos** (junto con Administración) |
| Calidad e inocuidad | Ninguna propia: comparte casos y tareas con Atención y Ventas |
| Solo lectura | Ninguna |

Si el cliente dice que una persona hace dos de estos papeles, el sistema ya lo permite: se le asigna el
rol con la llave que necesita. Lo que **no** se puede hoy es partir una llave a la mitad (por ejemplo,
que alguien autorice compras pero no vea el historial): son tres permisos que van juntos en el rol
`admin`.

### 2. El pase de trabajo más importante no existe en el sistema

**De Almacén a Abastecimiento.** VERIFICADO: cuando una existencia baja del mínimo, el aviso le llega a
Almacén. Pero **el sistema no tiene ninguna forma de que Almacén le avise a Abastecimiento**: no hay
mensajes entre áreas, no hay "solicitud de compra", y el aviso de bajo mínimo **no** va dirigido a
Abastecimiento. Hoy ese paso ocurre de viva voz.

INFERIDO: en una empresa chica eso funciona porque se ven todos los días. En cuanto crezca, es donde se
van a perder las compras. Es el hueco más visible del diagrama general.

### 3. Los pases de trabajo que sí están resueltos

- **Ventas → Administración:** al ganar una oportunidad, el sistema **crea sola** una tarea para
  Administración. VERIFICADO. Es el único pase de trabajo automático entre dos áreas.
- **Ventas → Almacén:** el pedido confirmado aparece en la lista de Almacén, listo para surtir.
- **Abastecimiento → Administrador:** la orden sobre el umbral aparece como "por autorizar".
- **Abastecimiento → Almacén:** la recepción crea el lote y la entrada, así que Almacén ya lo ve contado.

### 4. Tres personas dependen de que alguien capture un número

Y si nadie lo captura, el sistema se queda callado sin avisar que está callado:

1. **Mantenimiento** depende de que alguien capture el **odómetro**. Sin eso, el plan por kilómetros
   nunca avisa. El plan por días sí, porque el calendario avanza solo. VERIFICADO.
2. **Administración** depende de que alguien capture el **folio de la factura**. El sistema no lo pide
   ni lo reclama.
3. **Todos** dependen de que alguien pulse **"Revisar ahora"**, porque no hay tarea programada. Y ese
   botón solo lo tienen el Administrador y Administración. VERIFICADO.

### 5. El rol "solo lectura" no es tan de solo lectura

VERIFICADO con pruebas: **puede silenciar avisos y marcarlos leídos** (UI-4, decidido en D-60 que debe
exigir permiso de escritura del módulo, todavía sin implementar). Eso es lo contrario de lo que su
nombre promete, y está dibujado así en su diagrama.

También **podía descargar cualquier documento**, incluido un comprobante de caja o de un expediente.
**Eso quedó arreglado el 26-sep-2026** (SEC-1, decisión D-59): ahora un adjunto exige el permiso de
lectura del módulo dueño, con 15 pruebas que lo fijan. El diagrama `21_uso_lectura.mmd` conserva la
caja roja como registro de lo que pasaba, con la nota de que ya está resuelto.

---

## Preguntas nuevas que salieron de esta fase

PENDIENTES todas. Van además de las que ya están en `docs/BACKLOG.md`.

1. **¿Cómo le avisa hoy Almacén a Abastecimiento que hay que comprar?** (El hueco del punto 2.)
2. **¿Una sola persona cubre varios de estos papeles?** Si sí, ¿cuáles? Define si sobran roles o si
   falta combinarlos.
3. **¿Quién captura el kilometraje de los camiones, y cada cuándo?**
4. **¿Quién trabaja desde el celular?** Sospecho que Almacén con la mercancía enfrente y Mantenimiento
   en el taller son los dos casos claros, pero es INFERIDO.
5. **¿El director quiere ver el historial sin poder editar nada?** Eso es el rol "auditor" que ya está
   anotado como AUD-4.
6. **¿Qué número mira primero el director al entrar?** Hoy el tablero es igual para todos (UI-3).

---

## Los diez roles quedaron cubiertos

La primera versión de esta fase traía ocho. Se agregaron los dos que faltaban por decisión de Erick el
26-sep-2026, porque **Calidad es quien atiende una reclamación con número de lote** y sin ese recorrido
el rastreo por lote no se ve en ninguna parte:

| Archivo | Rol | Frase (INFERIDA) |
|---|---|---|
| `23_uso_atencion.mmd` | Atención a clientes | "Es donde aterriza todo lo que llega: clasifico el correo, doy de alta al que pregunta y abro el caso al que tiene un problema" |
| `24_uso_calidad.mmd` | Calidad e inocuidad | "Es donde sigo cada reclamación hasta saber de qué lote salió el producto y qué se hizo al respecto" |

**Lo que aporta el recorrido de Atención:** es la única, junto con Administración, que puede **cargar
correos**, y es la puerta de entrada de los cuatro canales. VERIFICADO que **no puede convertir** un
prospecto: eso lo pasa a Ventas. Y que el sistema nunca aplica una sugerencia del clasificador sola.

**Lo que aporta el recorrido de Calidad, y es lo más valioso:** al atender una reclamación con lote,
puede *ver* el inventario y rastrear por los movimientos de salida **a qué otros clientes se les vendió
ese mismo lote**. Ese es el rastreo que pide FSSC 22000 y hoy funciona. Pero aparecen dos huecos que no
había visto en las otras fases:

1. **No puede bloquear un lote sospechoso** para que no se venda. No existe esa función. INFERIDO: en
   una empresa de alimentos, es lo primero que se quiere hacer al recibir una queja.
2. **El sistema tampoco impide vender un lote ya caducado.** VERIFICADO: `move()` no compara la fecha
   de caducidad con hoy; las caducidades solo alimentan avisos, que son informativos.

Sumado a RN-2 (no se puede registrar la devolución), el circuito de una reclamación queda abierto por
los dos extremos: no se puede frenar el lote ni recibir de vuelta el producto.
