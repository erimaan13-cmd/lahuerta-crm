# 09 · Recorrido por rol — qué ve y qué puede hacer cada empleado

Septiembre 2026. Informe de la Fase 1 del trabajo de documentación. Sustituye cualquier suposición
previa sobre visibilidad por rol; en particular corrige la sección 3 de `08_GUION_DOCUMENTACION.md`.

Etiquetas de evidencia: **VERIFICADO** = comprobado en el código o viendo el sistema correr ·
**INFERIDO** = razonamiento que puede estar equivocado · **PENDIENTE** = falta confirmación del cliente.

## Método

Se sembraron los datos de demostración (`python -m app.seed`), se levantó el servidor y se entró con
**los 12 usuarios del README**, uno por uno. Para cada usuario se solicitaron las 17 pantallas del
menú: 204 visitas en total, todas registradas en la bitácora. La matriz de permisos se leyó de
`app/permissions.py`.

---

## 1. El menú casi no distingue entre roles (decidido: así se queda)

**VERIFICADO.** Los 12 usuarios ven **las mismas 13 pestañas**, con tres excepciones:

| Quién | Pestañas | Añade |
|---|---|---|
| Ventas, Atención, Calidad, Almacén, Abastecimiento, Mantenimiento, Solo lectura | 13 | — |
| Recursos Humanos | 14 | Personal |
| Administración | 14 | Caja chica |
| Administrador (`admin`, `director`) | 17 | Personal, Caja chica, Historial, Usuarios |

Es decir: el almacenista ve Prospectos, Cuentas, Oportunidades, Correos y Casos; el vendedor ve
Inventario, Abastecimiento y Mantenimiento. Lo único reservado son los expedientes de personal, la
caja chica, el historial y la administración de usuarios.

**Decisión de Erick (25-sep-2026):** la visibilidad cruzada se conserva a propósito. Un vendedor debe
poder consultar la existencia antes de prometer una entrega. Ver D-57.

**La diferencia real entre roles está en lo que pueden escribir, no en lo que ven.** VERIFICADO con un
ejemplo: en Abastecimiento, el rol `abastecimiento` ve el formulario "Nueva orden de compra" con su
botón "Crear orden en borrador"; el rol `almacen` ve la misma lista de órdenes sin ese formulario.

---

## 2. Qué escribe cada rol

**VERIFICADO**, leído de `app/permissions.py`.

| Rol | Escribe | Solo mira |
|---|---|---|
| Ventas | Prospectos (y los convierte), cuentas, oportunidades, cotizaciones, pedidos, casos, tareas | Inventario, abastecimiento, mantenimiento |
| Atención a clientes | Prospectos, casos, tareas, carga de correos | Ventas, inventario, operación |
| Calidad e inocuidad | Casos, tareas | Todo lo demás |
| Administración | Caja chica, órdenes de compra, pedidos, casos, carga de correos | Inventario, personal, mantenimiento |
| Almacén | Movimientos de inventario, tareas | Todo lo comercial |
| Abastecimiento | Órdenes de compra, inventario, tareas | Todo lo comercial |
| Recursos Humanos | Expedientes, contratos, puestos, tareas | Todo lo demás |
| Mantenimiento | Activos, planes, órdenes de trabajo, tareas | Todo lo demás |
| Solo lectura | **Silenciar y marcar leídos los avisos** (ver corrección abajo) | Todo salvo personal, caja chica e historial |
| Administrador | Todo | — |

Todos los roles **menos "solo lectura"** pueden además subir adjuntos (`attachment:write`) y registrar
actividades.

### Corrección a la primera versión de este informe

La primera versión decía que el rol "solo lectura" no escribe nada. **Es falso.** Silenciar un aviso y
marcarlo leído solo exigen `notification:read` (`app/routers/notifications.py:39` y `:31`), permiso que
está en `BASE_READ` y por tanto tienen los diez roles. VERIFICADO con prueba: entrando como
`direccion@demo.local` (rol `lectura`) se silenció un aviso por 30 días y la fila quedó escrita en la
base de datos. La fila de prueba se eliminó después.

El código lo hace a propósito y lo comenta (`app/routers/notifications.py:42`): *"Silenciar es una
decisión del área, no del administrador: basta con poder ver los avisos"*. INFERIDO: el razonamiento
es sensato para las áreas operativas, pero deja que un usuario de consulta apague una alerta de lote
por caducar. PENDIENTE de decidir con Erick; anotado como UI-4.

Generar los avisos, en cambio, exige `integration:run`, que solo tienen `admin` y `administracion`.

---

## 3. Ninguna pantalla sale vacía con los datos de demostración

**VERIFICADO.** Renglones devueltos por pantalla (incluyen el encabezado de la tabla): Prospectos 8,
Cuentas 8, Pedidos 17, Correos 19, Casos 3, Inventario 15, Mantenimiento 7, Tareas 12, Personal 9,
Caja chica 4, Documentos 4, Historial 101.

Dos aclaraciones sobre la medición, para que nadie las malinterprete:

- **Oportunidades devuelve cero renglones de tabla y no está vacía.** Es un tablero kanban de 8
  columnas (una por etapa) con 7 tarjetas, cada una con enlace a su detalle. Los identificadores son
  UUID, no números. VERIFICADO.
- **Avisos es la única pantalla que se adapta al rol por sí sola**: 13 avisos para el administrador,
  10 para Almacén, 9 para Mantenimiento, 8 para el resto. VERIFICADO.

---

## 4. Dónde se atora alguien que nunca usó un sistema así

1. **El mensaje de bloqueo habla en clave.** VERIFICADO: al entrar a una sección ajena se lee *"No se
   pudo completar la acción — Tu rol no tiene el permiso 'pettycash:read'"*. Un almacenista no sabe
   qué es `pettycash:read`. Anotado en el backlog.
2. **Rara vez llegará a ese mensaje**, porque el menú esconde lo que no puede abrir: solo lo verá
   quien escriba una dirección a mano o siga un enlace ajeno. VERIFICADO. INFERIDO: gravedad baja.
3. **El menú de 13 pestañas sin jerarquía es el riesgo real.** Alguien de almacén ve cinco secciones
   comerciales antes de llegar a Inventario. INFERIDO. Anotado en el backlog.
4. **El tablero es la pantalla de inicio de todos y la más densa** (22 renglones de tarjetas y
   tablas). VERIFICADO. Útil para ventas, ruido para un mecánico. Anotado en el backlog.
5. **Dos usuarios comparten rol y nada lo indica**: `admin@demo.local` y `director@demo.local` tienen
   permisos idénticos, igual que `ventas1` y `ventas2`. VERIFICADO. Confunde al demostrar el sistema.

---

## 5. Preguntas abiertas para el cliente

**PENDIENTE**, todas. No se responden leyendo el código.

1. **¿Quién aprueba las compras: el dueño, o hace falta un rol de jefe de compras que autorice sin
   poder crear órdenes?** VERIFICADO que hoy el permiso `procurement:authorize` lo tiene únicamente
   el administrador. Decisión de Erick (25-sep-2026): **no se cambia**, es separación de funciones —
   darle esa llave a Abastecimiento le permitiría aprobar sus propias compras. Ver D-58.
2. **¿El umbral de $20,000 MXN para exigir autorización es el real?** Hoy es un valor provisional.
3. **¿Existen de verdad las diez áreas?** Los roles se infirieron de un organigrama; puede que una
   sola persona haga almacén y compras.
4. **¿Quién trabajará en computadora y quién en celular?** Cambia qué pantalla conviene optimizar.
5. **¿Quién captura los correos?** Hoy pueden Atención y Administración. PENDIENTE si el buzón sigue
   siendo uno solo (`administracion@`).
