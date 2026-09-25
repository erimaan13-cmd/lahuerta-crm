# 08 · Guion de documentación (guía de uso, video y diagrama)

Septiembre 2026. Este documento **no es la guía de uso**: es la materia prima de los tres
entregables que Erick pidió y que se producen después de las mejoras de interfaz.

| Entregable | Herramienta | Qué toma de aquí |
|---|---|---|
| Guía de uso | documento | Todo: significados, flujos, quién hace qué |
| Video de uso | Hyperframes | Los recorridos de la sección 4, en el orden en que están |
| Esquema de construcción, flujos y usos | Lucidchart | Las secciones 2 y 5 |

Regla que lo motiva: **lo que necesita explicación no se explica en pantalla.** El cliente evalúa
el sistema viéndolo; un párrafo didáctico junto a cada botón es ruido para él. La explicación vive
aquí y en los tres entregables.

Etiquetas de evidencia: VERIFICADO = comprobado en el código durante esta sesión ·
INFERIDO = razonamiento que puede estar equivocado · PENDIENTE = falta confirmación del cliente.

---

## 1. Oportunidades por etapa: qué significa cada una y si aplica

La pestaña **Oportunidades** sigue una oportunidad de venta desde que el cliente pregunta hasta que se
gana o se pierde. Las ocho etapas están programadas en `app/services/pipeline.py` (VERIFICADO).

| Etapa | Qué significa en el negocio | ¿Aplica a La Huerta? |
|---|---|---|
| **Requerimiento** | El cliente dijo qué necesita: producto, kilos aproximados, para cuándo. Todavía no hay número. | Sí, siempre. Es el punto de entrada de todo prospecto calificado. |
| **Desarrollo de fórmula** | El cliente pide una mezcla o especificación propia (sazonador para una marca, granulometría especial) y hay que formularla. | Solo en pedidos especiales. INFERIDO: en venta de producto de catálogo esta etapa se salta. |
| **Muestra enviada** | Se mandó producto físico para que lo prueben. | Sí, en cliente nuevo o producto nuevo. Se salta en recompra. |
| **Muestra aprobada** | El cliente confirmó que la muestra sirve. Sin esto no tiene sentido cotizar volumen. | Sí, cuando hubo muestra. |
| **Cotización** | Hay un precio por escrito, con vigencia. | Sí, siempre. |
| **Negociación** | El cliente respondió a la cotización: pide descuento, cambia volumen, discute plazo. | Sí, es donde se gana o se pierde el margen. |
| **Ganada** | Se convirtió en pedido. | Sí. Cierra la oportunidad. |
| **Perdida** | El cliente no compró. Se registra el motivo. | Sí. Sirve para saber si se pierde por precio, por plazo o por no tener el producto. |

**Cómo leerlo.** Una etapa con muchas oportunidades detenidas es un cuello de botella: si hay ocho
en "Muestra enviada" y ninguna en "Muestra aprobada", nadie está dando seguimiento a las muestras.

**Saltarse etapas es normal.** El sistema no obliga a pasar por las ocho; una recompra de producto
de catálogo puede ir de Requerimiento a Cotización.

**PENDIENTE de decidir con el cliente:** si "Desarrollo de fórmula" y "Muestra aprobada" se usan lo
suficiente o conviene fundirlas con las vecinas. Es una decisión de negocio, no técnica: quitar una
etapa es cambiar una línea.

---

## 2. Qué hace cada botón que no se explica solo

### Correos clasificados

| Botón | Qué hace | Para qué sirve |
|---|---|---|
| **Cargar correos de ejemplo** | Trae el buzón de demostración incluido en el sistema y lo clasifica. | Ver la pantalla con datos sin conectar un correo real. Es solo para la demostración. |
| **Archivo del correo (.eml)** + **Clasificar este correo** | Sube **un** mensaje guardado en formato `.eml` y lo pasa por el clasificador. | Probar el clasificador con un correo real de La Huerta sin conectar el buzón. Un `.eml` es lo que genera Outlook o Gmail al guardar un mensaje como archivo. |

**Lo que no hace, y hay que decirlo en el video:** el sistema **no** responde, borra, archiva ni
modifica buzones. Solo lee y sugiere. Cualquier sugerencia se aplica con clic humano (regla 3 del
proyecto, VERIFICADO).

### Historial completo

Tres filtros que parecen lo mismo y no lo son:

- **Tipo de evento** — la naturaleza de lo ocurrido: *Cambios de datos*, *Consultas y envíos*,
  *Seguridad*, *Sistema*.
- **Sobre qué registro** (búsqueda avanzada) — en qué vive el evento: un prospecto, una cuenta, un
  pedido, una pantalla visitada.
- **El nombre técnico del evento contiene** (búsqueda avanzada) — texto libre sobre el identificador
  interno (`lead.stage`, `auth.login`). Es para quien audita el código, no para el uso diario; por
  eso está plegado.

**Columnas:** *Detalle* es el "qué cambió" (`etapa: nuevo → contactado`) y es la razón de ser de la
bitácora. *IP* solo importa para revisar accesos raros; se oculta en celular y se conserva en el
CSV. El *Usuario* de cada renglón se guarda como correo congelado al momento del evento (D-31): si
alguien cambia de nombre o de área, su historial anterior no se reescribe.

### Abastecimiento

**Crear orden en borrador** deja la orden editable. Al enviarla, solo pide autorización si supera el
umbral configurado (hoy $20,000 MXN, PENDIENTE de confirmar con el cliente).

### Avisos

**Revisar ahora** recorre las seis reglas (contratos, documentos, lotes, existencias, mantenimientos
y tareas). Correrlo dos veces no duplica avisos. **Silenciar** oculta ese aviso y evita que vuelva a
generarse durante los días indicados.

---

## 3. Quién ve qué (para el diagrama de roles)

**El sistema tiene visibilidad cruzada a propósito (D-57): todos los roles ven las mismas 13
pestañas.** La razón es operativa: un vendedor debe poder consultar la existencia antes de prometer
una entrega, y quien atiende un reclamo debe poder ver el lote que salió. Lo que cambia entre roles
**no es lo que ven, sino lo que pueden escribir**.

Solo cuatro secciones están reservadas:

| Sección reservada | Quién entra | Por qué |
|---|---|---|
| Personal (expedientes) | RRHH y administradores | Datos personales (D-40); falta el aviso de privacidad |
| Caja chica | Administración y administradores | Montos y comprobantes (D-40) |
| Historial | Solo administradores | Regla 1 del proyecto |
| Usuarios | Solo administradores | Altas, bajas y cambios de rol |

Quién **escribe** en cada módulo:

| Rol | Escribe |
|---|---|
| Almacén | Movimientos de inventario, tareas |
| Abastecimiento | Órdenes de compra, inventario, tareas |
| Ventas | Prospectos (y los convierte), cuentas, oportunidades, cotizaciones, pedidos, casos, tareas |
| Atención a clientes | Prospectos, casos, tareas, carga de correos |
| Calidad | Casos, tareas |
| RRHH | Expedientes, contratos, puestos, tareas |
| Administración | Caja chica, órdenes de compra, pedidos, casos, carga de correos |
| Mantenimiento | Activos, planes, órdenes de trabajo, tareas |
| Solo lectura | Solo puede silenciar y marcar leídos los avisos (ver nota) |
| Administrador | Todo, incluidos historial y usuarios |

**Nota sobre los avisos:** silenciar y marcar leído exigen únicamente `notification:read`, que tienen
los diez roles, así que **incluso "solo lectura" puede apagar una alerta**. Está hecho a propósito
(silenciar es decisión del área), pero conviene revisarlo: anotado como UI-4. **Generar** los avisos sí
está restringido a `admin` y `administracion` (`integration:run`).

Autorizar una orden de compra (`procurement:authorize`) es **solo del administrador**, y es
deliberado: si Abastecimiento tuviera esa llave podría aprobar sus propias compras (D-58).

Cada consulta a personal y a caja chica **queda registrada en la bitácora**. El detalle completo del
recorrido por rol está en `09_RECORRIDO_POR_ROL.md`.

---

## 4. Recorridos para el video (orden sugerido)

Cada recorrido dura entre 40 y 90 segundos. Se graban en el entorno de demostración, nunca con datos
reales.

1. **Entrar y orientarse.** Acceso, tablero, qué dice cada tarjeta, dónde está el menú en
   computadora y en celular.
2. **Un prospecto se vuelve pedido.** Alta de prospecto → tarea de primer contacto → oportunidad → etapas del
   Oportunidades (aquí se explica la sección 1) → cotización → pedido.
3. **El pedido descuenta inventario.** Pedido con renglones → entrega → movimiento de salida → la
   existencia baja → por qué no puede quedar negativa.
4. **Comprar para reponer.** Orden de compra en borrador → autorización por monto → recepción →
   entrada a inventario con lote y caducidad.
5. **Los avisos.** Qué los genera, cómo se silencian, por qué todavía no salen por correo.
6. **Caja chica.** Gasto con comprobante obligatorio → saldo → exportación para el contador.
7. **Personal.** Expediente, contrato, aviso a 60 días. Mencionar el aviso de privacidad PENDIENTE.
8. **Historial completo.** Filtrar por área y usuario, qué significa cada columna, integridad de la
   cadena.
9. **En el celular.** Las mismas pantallas: menú deslizante, tablas como fichas, barra inferior.

---

## 5. Esquema de construcción (para Lucidchart)

**Tres capas, una sola dirección.**

```
navegador  →  rutas (app/main.py, app/routers/*.py)
              ↓ validan permisos y forma; no deciden reglas
           →  servicios (app/services/*.py)
              ↓ aplican las reglas, registran en la bitácora, confirman la transacción
           →  modelos (app/models.py)  →  base de datos
```

**Piezas transversales:** `app/web.py` (plantillas, sesión, permisos, CSRF), `app/permissions.py`
(qué puede cada rol), `app/audit.py` (bitácora encadenada SHA-256), `app/classifier/` (clasificador
de correo, no toca la base de datos), `app/integrations/` (correo de solo lectura, ERP simulado).

**Reglas que el diagrama debe hacer evidentes:**

1. Ningún módulo escribe en las tablas de otro. Pedidos y compras tocan el inventario únicamente a
   través de `inventory.move()`.
2. Toda mutación llama a `audit.record(...)`. No existe ninguna ruta que edite o borre la bitácora.
3. La existencia es la suma de los movimientos, nunca una columna de saldo (D-34).
4. El sistema no emite facturas fiscales: La Huerta factura en CONTPAQi y aquí se captura el folio
   (D-37).

---

## 6. Lo que la documentación debe dejar claro y hoy no se dice en pantalla

- El significado de cada etapa de Oportunidades y que saltárselas es normal (sección 1).
- Que "Cargar correos de ejemplo" es de demostración y no toca ningún buzón real.
- Qué es un archivo `.eml` y de dónde sale.
- La diferencia entre *Tipo de evento*, *Sobre qué registro* y el texto libre del historial.
- Que los avisos todavía no salen por correo y por qué.
- Que los expedientes y la caja chica son visibles solo para su área, y que consultarlos deja huella.
