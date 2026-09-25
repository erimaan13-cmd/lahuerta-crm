# 06 · Operación interna (inventario, ventas, abastecimiento, RRHH, caja chica, mantenimiento)

Septiembre 2026. Esta iteración convierte el CRM en el **sistema interno** que pidió La Huerta.
El CRM comercial (prospectos, cuentas, oportunidades, correos) sigue igual y pasa a ser un módulo más.

Fuente de las decisiones: `claude/AT-15` del proyecto Administración Tecnológica, con las respuestas
de Erick del 23-sep-2026. Lo marcado PENDIENTE sigue esperando respuesta del cliente.

## 1. Qué hace cada módulo

| Módulo | Ruta | Para qué sirve | Quién escribe |
|---|---|---|---|
| Inventario | `/inventario` | Existencia por producto, lote y bodega; movimientos; alertas de mínimo y caducidad | almacén, abastecimiento |
| Abastecimiento | `/abastecimiento` | Órdenes de compra a proveedores, autorización, recepción que entra a inventario | abastecimiento, administración |
| Pedidos (ventas) | `/ventas` | Pedido con renglones que descuenta inventario al entregarse; folio de la factura externa | ventas, administración |
| Mantenimiento | `/mantenimiento` | Activos (camiones, climas, equipos), planes por días/km/horas, órdenes de trabajo, documentos | mantenimiento |
| Personal | `/rrhh` | Expedientes, puestos por puntos, contratos y sus vencimientos | RRHH |
| Caja chica | `/caja` | Fondo fijo, gastos con comprobante obligatorio, reposiciones, exportación al contador | administración |
| Avisos | `/avisos` | Todo lo que está por vencer o ya venció, con opción de silenciar | todos (según su área) |
| Documentos | `/documentos` | Escaneos con vencimiento de cualquier registro | todos (según su área) |

## 2. Reglas de negocio que quedaron programadas

1. **La existencia es la suma de los movimientos**, no una columna que alguien pueda corregir a mano.
   Cada entrada, salida, ajuste o traspaso guarda quién, cuándo, cuántos kilos y por qué.
2. **Nunca hay existencia negativa.** Si un pedido intenta sacar más de lo que hay, la operación se
   rechaza con un mensaje que dice cuánto hay y cuánto se pedía.
3. **La unidad se configura por producto** (kilo, saco, caja, tarima) y siempre se guarda su
   equivalencia en kilos, porque el negocio reporta en kilos.
4. **Surtido por caducidad:** si el renglón del pedido no indica lote, se surte primero el lote que
   caduca antes. En alimentos, lo contrario es tirar producto.
5. **El sistema no factura.** Emitir CFDI exige certificados fiscales y un proveedor autorizado; La
   Huerta ya factura en CONTPAQi. Aquí solo se captura el folio de esa factura.
6. **Una orden de compra solo pide autorización arriba de un monto** (`CRM_PO_AUTH_THRESHOLD_MXN`,
   hoy $20,000 PENDIENTE de confirmar). Con 7 a 15 empleados, una cadena de autorizaciones larga
   estorba más de lo que protege.
7. **Un gasto de caja chica sin comprobante no se registra**, y ningún gasto puede dejar la caja en
   negativo.
8. **Contratos:** aviso semanal desde dos meses antes del vencimiento, dirigido a RRHH y a los
   administradores, con opción de silenciarlo.
9. **Mantenimiento:** vence lo que ocurra primero, fecha, kilómetros u horas de uso.
10. **Los expedientes de personal solo los ven RRHH y los administradores**, y cada consulta queda
    registrada en la bitácora. La caja chica solo la ve administración.
11. **Los documentos se guardan tal cual**: sin OCR. Si traen fecha de vencimiento, generan aviso.
12. **Los avisos no se envían por correo todavía**: quedan en cola con estado `sin_adaptador`.
    Cuando se configure el envío, el único punto a tocar es `app/services/notifications.py`.

## 3. Cómo está hecho

```
app/services/     inventory.py · procurement.py · sales.py · maintenance.py · hr.py · pettycash.py
                  notifications.py · files.py
app/routers/      un archivo por módulo (APIRouter); main.py los registra con una línea
app/web.py        piezas compartidas por todas las rutas (plantillas, sesión, permisos, CSRF)
```

Las rutas solo validan permisos y delegan en los servicios; los servicios validan reglas, registran
en la bitácora y confirman la transacción. Ningún módulo escribe en las tablas de otro: los pedidos y
las compras tocan el inventario a través de `inventory.move()`.

## 4. Roles nuevos

`almacen` · `abastecimiento` · `rrhh` · `mantenimiento`, además de los seis que ya existían.
Cada uno ve todo lo operativo de lectura, menos personal y caja chica, y solo escribe en lo suyo.

## 5. Avisos: cómo se generan

`POST /avisos/generar` (o `python -m app.services.notifications` desde una tarea programada diaria)
recorre seis reglas: contratos por vencer, documentos por vencer, lotes por caducar, existencias bajo
el mínimo, mantenimientos programados y tareas vencidas. Es idempotente: la clave de cada aviso
incluye el periodo (semana o día), así que correrlo varias veces no duplica nada.

## 6. Lo que falta (PENDIENTE del cliente)

- Producto y versión exactos de CONTPAQi, para decidir la pestaña de facturación (leer el XML del
  CFDI en la fase 1, conector con el SDK en la fase 2).
- Monto a partir del cual una orden de compra requiere autorización.
- Qué se lleva hoy en Excel y hay que migrar.
- Texto faltante del cliente en "PRODUCTOS: *****".
- Aviso de privacidad para empleados y política de uso del sistema: obligatorios **antes** de cargar
  expedientes reales.
