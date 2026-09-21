# 01 · Investigación — Empacadora La Huerta

> Fase EXPLORAR. Fecha de consulta: 21-sep-2026 (≈02:10 h, Monterrey).
> Ningún dato de este documento es oficial de la empresa salvo los marcados **VERIFICADO** con URL. El organigrama y los procesos son **reconstrucciones inferidas**.

## Conclusión corta

La Huerta es un distribuidor/procesador **100 % B2B por volumen (≥ 500 kg)** de especias, granos, chiles secos, semillas y condimentos, con **molienda propia, fórmulas personalizadas, stock de seguridad (< 72 h)** y **certificación FSSC 22000**. Su captación pública pasa por **dos formularios web, un teléfono/WhatsApp y un único correo (`administracion@`)**. Eso define el CRM: pocas fuentes de entrada que hoy convergen en un buzón compartido, un ciclo comercial con un **subflujo de desarrollo de fórmula/muestra**, y una relación postventa donde **calidad (lotes, certificados, reclamaciones)** y **logística** generan interacciones que el CRM debe ver, pero no gobernar.

Leyenda de etiquetas:
- **HECHO VERIFICADO** — leído hoy en la fuente primaria.
- **INFERENCIA FUERTE** — varias evidencias o una evidencia + requisito normativo conocido.
- **INFERENCIA DÉBIL** — una evidencia indirecta o analogía sectorial.
- **DESCONOCIDO** — requiere validación interna.
- **RECORDADO** — lo informó Erii en sesiones previas (no verificado hoy).

---

## 1. Fuentes consultadas

| Fuente | URL | Resultado |
|---|---|---|
| Inicio (incluye sección "Nosotros" como ancla) | https://empacadoralahuerta.com/ | OK |
| Nosotros (ruta dedicada) | https://empacadoralahuerta.com/nosotros/ | **404** — el contenido vive en `/#nosotros` |
| Certificación | https://empacadoralahuerta.com/certificacion/ | OK |
| Catálogo (lead magnet) | https://empacadoralahuerta.com/catalogo-2/ | OK — no muestra productos; pide datos para descargar |
| Contacto | https://empacadoralahuerta.com/contacto/ | OK |
| Aviso de privacidad | https://empacadoralahuerta.com/aviso-de-privacidad/ | OK |
| SimplyHired (perfil empresa) | https://www.simplyhired.mx/browse-jobs/companies/Empacadora-La-Huerta | OK — solo nombres de puestos con datos salariales, sin vacantes activas |
| LinkedIn (página empresa) | https://www.linkedin.com/company/empacadora-la-huerta | **Bloqueado por robots.txt**; existencia RECORDADA |
| Salesforce "¿Qué es CRM?" | https://www.salesforce.com/mx/crm/what-is-crm/ | OK |
| Búsquedas web (registro, vacantes, directorios) | — | Sin fuentes adicionales útiles; aparece un **homónimo** (Frigorizados La Huerta S.A. de C.V.) que se **excluye** |

Limitación técnica: la descarga directa (curl) del sitio fue rechazada por el proxy (`CONNECT tunnel failed, response 403`); se leyó mediante la herramienta de lectura web, que no expone las **opciones de los `<select>`** ("Especifica tu sector", "Producto de interés"). Esas listas quedan **DESCONOCIDAS**.

---

## 2. EVIDENCE_LEDGER

| ID | Hallazgo | Área / proceso | Fuente | URL | Evidencia encontrada | Tipo | Confianza | Implicación para el CRM |
|---|---|---|---|---|---|---|---|---|
| E01 | Importa y distribuye especias, granos y condimentos para industria alimentaria, hoteles, restaurantes y comedores | Mercado / segmentación | Inicio | https://empacadoralahuerta.com/ | "Importamos y distribuimos Especias, granos y condimentos… para Industrias alimentarias, sector hotelero, restaurantes y comedores." | Verificado | Alto | Catálogo `Sector` con 4 valores base; `Account.sector` obligatorio al calificar |
| E02 | Venta exclusiva por volumen desde 500 kg; alcance nacional | Ventas / calificación | Inicio | https://empacadoralahuerta.com/ | "Socio estratégico a nivel nacional. Venta exclusiva por volumen desde 500 kg." | Verificado | Alto | Regla de calificación: volumen estimado ≥ 500 kg; bandera "bajo mínimo"; `city/state` para cobertura nacional |
| E03 | Certificación FSSC 22000 por Global Certification Bureau, vigente hasta jul-2028 | Calidad / inocuidad | Certificación | https://empacadoralahuerta.com/certificacion/ | "FSSC 22000"… vigencia "julio 2028" | Verificado | Alto | Las reclamaciones requieren trazabilidad a lote → `Case.lot_reference`; solicitudes de certificados son interacciones frecuentes |
| E04 | Alcance certificado: almacenamiento, acondicionamiento y distribución de semillas, granos, especias, chiles secos y condimentos | Operaciones | Certificación | https://empacadoralahuerta.com/certificacion/ | Alcance: almacenamiento, acondicionamiento, distribución | Verificado | Alto | Existen procesos operativos formales (fuera del CRM) → solo referencias/estados vía integración |
| E05 | Stock de seguridad; entregas < 72 h | Inventario / logística | Inicio | https://empacadoralahuerta.com/ | "Stock de seguridad: Tiempos de entrega menores a 72 horas." | Verificado | Alto | Promesa de servicio medible: `OrderReference.promised_date` y SLA de entrega visibles en la cuenta |
| E06 | Fórmulas personalizadas con equipo especializado | Desarrollo de producto | Inicio | https://empacadoralahuerta.com/ | "Contamos con un equipo especializado que te ayudará a crear el condimento o sazonador…" | Verificado | Alto | Subflujo de oportunidad: requerimiento → desarrollo → muestra → aprobación → cotización |
| E07 | Molienda in-house para asegurar especificaciones | Producción / calidad | Inicio | https://empacadoralahuerta.com/ | "Molienda in-house" | Verificado | Alto | El CRM captura la especificación requerida (malla/granulometría, etc.) como texto del requerimiento; producción vive fuera |
| E08 | Productos nacionales e importados; compra directa a proveedores certificados | Compras / importaciones | Inicio | https://empacadoralahuerta.com/ | "Productos Nacionales e Importados… proveedores certificados" | Verificado | Alto | Correos de proveedores llegan al mismo buzón → categoría `PROVEEDOR_COMPRAS` se enruta fuera del CRM |
| E09 | Líneas: especias, granos (arroz y frijol), semillas, chiles secos, condimentos/sazonadores | Catálogo | Inicio + Catálogo | https://empacadoralahuerta.com/catalogo-2/ | "semillas, granos, especias, chiles secos y condimentos" | Verificado | Alto | `Product` con `category`; lista de productos concretos DESCONOCIDA → catálogo sintético editable |
| E10 | Empaques: saco polipropileno + bolsa PEAD; saco kraft triple capa + bolsa PE; caja de cartón corrugado | Empaque | Inicio | https://empacadoralahuerta.com/ | Tres opciones de empaque listadas | Verificado | Alto | `QuoteItem.packaging` (enum de 3 valores) |
| E11 | Presentaciones industriales desde 25 kg; personalización para marcas/cocinas; abasto ininterrumpido | Oferta comercial | Inicio | https://empacadoralahuerta.com/ | "Presentaciones industriales desde 25 kg", "Personalización", "Abasto ininterrumpido" | Verificado | Alto | Unidad base kg; presentaciones múltiplos de 25 kg; clientes recurrentes con abasto programado → recompra |
| E12 | Fundada en 2015; visión: "marca de confianza presente en los hogares" | Estrategia | Inicio | https://empacadoralahuerta.com/ | Año 2015; misión y visión | Verificado | Alto | Posible canal retail futuro (P2) — el modelo de cuenta no debe asumir solo B2B industrial |
| E13 | Contacto: Guadalupe N.L.; L–V 8:00–17:00; tel. 81 3551 2490; WhatsApp; `administracion@empacadoralahuerta.com` | Atención / canales | Contacto | https://empacadoralahuerta.com/contacto/ | Datos de contacto y horario | Verificado | Alto | Canales de entrada: web, teléfono, WhatsApp, correo; SLA calculado en horario hábil |
| E14 | Formulario de contacto/cotización: Nombre\*, Empresa, Email\*, Teléfono, Ciudad, Producto de interés, Mensaje | Captación | Contacto / Catálogo | https://empacadoralahuerta.com/contacto/ | "¿Tienes dudas o quieres cotizar un pedido? Déjanos tus datos y te contactaremos enseguida." | Verificado | Alto | Esquema mínimo de `Lead` = estos campos + `source=web_contacto`; "enseguida" → SLA de primer contacto |
| E15 | Formulario de descarga de catálogo: Nombre, Correo, Teléfono, Sector, Cantidad (500 kg–1 t / > 1 t) | Captación / marketing | Catálogo | https://empacadoralahuerta.com/catalogo-2/ | Select "Cantidad que quieres comprar" con dos rangos | Verificado | Alto | `Lead.volume_band` (enum) y `source=web_catalogo`; el catálogo es un lead magnet |
| E16 | Aviso de privacidad: datos de identificación, contacto y patrimoniales/financieros; finalidad: relación jurídica y comercial; no identifica área ARCO | Legal / privacidad | Aviso | https://empacadoralahuerta.com/aviso-de-privacidad/ | Categorías de datos y finalidades | Verificado | Alto | Consentimiento/origen del dato en `Lead`; derechos ARCO → exportar/anonimizar contacto (P1); no guardar datos financieros en CRM |
| E17 | El único correo público es `administracion@` | Atención / admin | Contacto | https://empacadoralahuerta.com/contacto/ | Un solo buzón publicado | Inferido (fuerte) | Medio | Buzón compartido mezcla ventas, compras, facturación y calidad → **justifica el clasificador** |
| E18 | Puestos asociados: Intendente, Ayudante general de almacén, Vendedor industrial, Vendedor, Ingeniero de alimentos | RR. HH. / estructura | SimplyHired | https://www.simplyhired.mx/browse-jobs/companies/Empacadora-La-Huerta | Lista de "puestos populares" (sin vacantes activas) | Verificado (secundaria) | Medio | Existe fuerza de ventas (industrial) y perfil técnico de alimentos → roles `ventas` y `calidad` en RBAC |
| E19 | Homónimo "Frigorizados La Huerta S.A. de C.V." no es la empresa | Control de evidencia | Búsqueda web | https://panjiva.com/Frigorizados-La-Huerta-SA-De-Cv/1096379 | Otra razón social y giro | Verificado | Alto | Excluir de la evidencia; deduplicación por dominio, no por nombre |
| E20 | La Huerta no tiene redes sociales (solo Google y web); tiene página de LinkedIn; piloto de pauta Google Search + Meta | Marketing | Erii (sesiones previas) | — | Información del proyecto de campaña | RECORDADO | Medio | `Lead.source` debe distinguir `google_ads`, `meta_ads`, `linkedin`, `organico` para medir la campaña |
| E21 | Sección "Nosotros" es un ancla del inicio; `/nosotros/` devuelve 404 | Sitio web | Sitio | https://empacadoralahuerta.com/nosotros/ | Error 404 | Verificado | Alto | Ninguna (nota de calidad del sitio) |
| E22 | Opciones de "Especifica tu sector" y "Producto de interés" no recuperables | Captación | Catálogo | https://empacadoralahuerta.com/catalogo-2/ | Herramienta no expone opciones | Desconocido | — | Catálogos `Sector` y `Product` deben ser **configurables**, no codificados |
| E23 | Razón social completa (p. ej. S.A. de C.V.) no confirmada | Legal | Aviso | https://empacadoralahuerta.com/aviso-de-privacidad/ | Solo "EMPACADORA LA HUERTA" | Desconocido | — | Ninguna para el MVP |
| E24 | La norma FSSC 22000 (ISO 22000 + PRP) exige trazabilidad, gestión de quejas y de producto potencialmente no inocuo/retiros | Calidad | Conocimiento normativo general (no consultado hoy) | — | Requisitos conocidos de la norma | Inferido (fuerte) | Medio | `Case` de tipo reclamación con lote, severidad y handoff obligatorio a Calidad (QMS) |
| E25 | Clientes de industria alimentaria suelen pedir fichas técnicas, certificados de análisis y constancias de certificación a proveedores | Calidad / atención | Práctica sectorial | — | Analogía sectorial | Inferido (débil) | Bajo | Categoría de correo `DOCUMENTACION_CALIDAD` distinta de reclamación |

---

## 3. Estructura organizacional inferida

> **No es un organigrama oficial.** Es una hipótesis de trabajo para diseñar roles y enrutamiento. Validar con la empresa.

### 3A. Organigrama inferido

| Nodo | Función | Evidencia | Confianza | Relación con otras áreas |
|---|---|---|---|---|
| Dirección General | Estrategia, alianzas "socio estratégico nacional", aprobación de precios especiales | E02, E12 | Inferencia fuerte (toda empresa la tiene; tamaño DESCONOCIDO) | Supervisa todas |
| Comercial / Ventas | Prospección, cotización, cuentas por volumen, vendedores industriales | E02, E14, E15, E18 | Inferencia fuerte | Recibe leads de Marketing/web; pide factibilidad a Operaciones y Desarrollo; entrega pedidos a Administración y Almacén |
| Atención a clientes | Primer contacto de formularios, teléfono, WhatsApp | E13, E14 ("te contactaremos enseguida") | Inferencia débil **como área separada** (probablemente la cubre Ventas o Administración) | Ventas, Administración |
| Administración (y facturación/cobranza) | Buzón `administracion@`, facturación, cobranza, datos financieros | E13, E16, E17 | Inferencia fuerte de la función; **DESCONOCIDO** si incluye cobranza | Ventas (condiciones), Compras (pagos), Dirección |
| Compras / Importaciones | Abasto nacional e importado, proveedores certificados | E08 | Inferencia fuerte | Almacén (recepción), Calidad (aprobación de proveedores), Administración (pagos) |
| Operaciones — Almacén e Inventario | Almacenamiento, stock de seguridad | E04, E05, E18 (ayudante de almacén) | Inferencia fuerte | Compras, Producción, Logística |
| Operaciones — Molienda, acondicionamiento y empaque | Molienda in-house, acondicionamiento, 3 tipos de empaque | E04, E07, E10 | Inferencia fuerte | Almacén, Calidad, Desarrollo |
| Calidad e Inocuidad | Sistema FSSC 22000, liberación de producto, reclamaciones, documentación | E03, E18 (ingeniero de alimentos), E24 | Inferencia fuerte | Todas las operativas; Ventas (reclamaciones, certificados) |
| Desarrollo / Formulación | Crear sazonadores a la medida | E06 ("equipo especializado") | Inferencia fuerte de la función; **inferencia débil** de que sea un área distinta de Calidad | Ventas (requerimiento), Calidad, Molienda |
| Logística / Distribución | Entregas < 72 h, distribución nacional | E02, E04, E05 | Inferencia fuerte de la función; **DESCONOCIDO** si es flota propia o paquetería/terceros | Almacén, Ventas, Administración |
| Marketing | Web, catálogo como lead magnet, pauta digital | E15, E20 | Inferencia fuerte; parcialmente **externo** (agencia/apoyo) — RECORDADO | Ventas |
| Servicios generales | Limpieza (intendencia) | E18 | Inferencia media | Operaciones |

Diagrama: `docs/diagrams/02_organigrama_inferido.mmd` (y versión Lucid; ver `docs/DIAGRAMAS.md`).

### 3B. Capability Map

Nivel de pertenencia al CRM: **A** = el CRM es sistema maestro · **B** = el CRM muestra referencia/estado · **C** = vive fuera; solo integración o enrutamiento.

| Dominio | Capacidad | Evidencia | Existencia | Pertenencia CRM |
|---|---|---|---|---|
| **Generación de demanda** | Marketing digital / campañas | E15, E20 | Fuerte | A (origen del lead, campaña) |
| | Captura de leads web (2 formularios) | E14, E15 | Verificado | **A** |
| | Prospección saliente (vendedor industrial) | E18 | Fuerte | **A** |
| **Gestión comercial** | Calificación (volumen, sector, cobertura) | E02, E15 | Fuerte | **A** |
| | Gestión de cuentas y contactos | E01 | Fuerte | **A** |
| | Oportunidades y pipeline | E14 ("cotizar un pedido") | Fuerte | **A** |
| | Cotizaciones | E14 | Fuerte | **A** (documento comercial; precio de lista puede venir del ERP) |
| | Negociación / precios especiales | E02 | Débil | A (registro), aprobación = P1 |
| | Cuentas clave / clientes recurrentes | E02, E11 ("abasto ininterrumpido") | Fuerte | **A** (segmentación, recompra) |
| **Desarrollo de producto** | Fórmulas personalizadas, muestras | E06 | Verificado | **A** para el seguimiento comercial (etapas, muestra aprobada); **C** para la fórmula técnica (receta, especificación) |
| **Cumplimiento del pedido** | Pedido de venta | E14 | Fuerte | **B** (`OrderReference` desde ERP) |
| | Inventario / stock de seguridad | E05 | Verificado | **C** (WMS/ERP); B solo "disponibilidad" futura |
| | Molienda, acondicionamiento, empaque | E04, E07, E10 | Verificado | **C** |
| | Distribución / entrega < 72 h | E05 | Verificado | **B** (estado y fecha de entrega) |
| **Abastecimiento** | Compras, proveedores, importaciones | E08 | Verificado | **C** (el CRM solo enruta correos de proveedores) |
| **Calidad e inocuidad** | Sistema FSSC 22000, lotes, liberación | E03, E24 | Verificado/fuerte | **C** (QMS) |
| | Reclamaciones de cliente | E24 | Fuerte | **A** para el caso con el cliente (registro, SLA, comunicación); **C** para la investigación/CAPA en QMS |
| | Documentación a clientes (fichas, certificados) | E03, E25 | Débil | A como solicitud/caso; archivos en QMS/DMS |
| **Finanzas** | Facturación (CFDI), cobranza | E16, E17 | Fuerte / desconocido | **B** (estado de crédito / saldo vencido como bandera, P1) — **C** el dato |
| **Administración** | Buzón compartido, privacidad ARCO | E16, E17 | Fuerte | A (clasificación de correo, consentimiento) |
| **Postventa** | Seguimiento, satisfacción, recompra | E11 | Fuerte | **A** |

Diagrama: `docs/diagrams/02b_capability_map.mmd`.

---

## 4. Procesos reconstruidos (end-to-end)

### 4.1 Flujo estándar (producto de catálogo)

| # | Paso | Actor | Entrada | Acción / decisión | Salida / dato | Handoff | Evidencia | Estado |
|---|---|---|---|---|---|---|---|---|
| 1 | Lead | Prospecto | Formulario web, WhatsApp, teléfono, correo | Envía datos | `Lead` (source) | Web → Ventas | E13–E15 | Verificado (canales) |
| 2 | Contacto | Ventas / atención | Lead | Primer contacto "enseguida" | `Activity` (llamada/correo) | — | E14 | Fuerte |
| 3 | Calificación | Ventas | Lead + conversación | ¿≥ 500 kg? ¿sector B2B? ¿ciudad atendible? | Lead calificado / descartado | — | E02, E15 | Fuerte |
| 4 | Necesidad | Ventas | Conversación | Producto, especificación (molienda), empaque, frecuencia, volumen | `Opportunity` + `ProductInterest` | Ventas ↔ Calidad (spec) | E07, E10, E11 | Fuerte |
| 5 | Cotización | Ventas (+ Dirección si precio especial) | Requerimiento | Precio por kg, empaque, flete, vigencia | `Quote` + `QuoteItem` | Ventas ← ERP (precios/stock) | E14 | Fuerte; **aprobaciones DESCONOCIDAS** |
| 6 | Negociación | Ventas / cliente | Cotización | Ajustes de precio/volumen/condiciones | Nueva versión de `Quote` | — | — | Débil |
| 7 | Ganada / perdida | Ventas | Decisión cliente | Cierre; motivo de pérdida | Opportunity cerrada | — | — | Fuerte |
| 8 | Alta de cliente | Administración | Cliente ganado | Datos fiscales, crédito | Cliente en ERP/facturación | **CRM → ERP** | E16 | Fuerte; datos fiscales fuera del CRM |
| 9 | Pedido | Cliente → Ventas/Admin | OC del cliente | Captura de pedido | Pedido en ERP → `OrderReference` en CRM | **CRM ↔ ERP** | E14 ("cotizar un pedido") | Fuerte |
| 10 | Coordinación operativa | Almacén / molienda / empaque | Pedido | Surtido desde stock de seguridad, molienda, empaque | Lote(s) asignados | ERP/WMS | E04, E05, E07 | Fuerte |
| 11 | Entrega | Logística | Pedido surtido | Envío < 72 h | Estado de entrega | WMS/ERP → CRM | E05 | Verificado (promesa) |
| 12 | Facturación / cobranza | Administración | Entrega | CFDI, cobranza | Estado de pago | ERP → CRM (bandera) | E16, E17 | Desconocido |
| 13 | Seguimiento | Ventas | Entrega | Satisfacción, próximas necesidades | `Activity`, `Task` | — | E11 | Fuerte |
| 14 | Incidencia / reclamación | Cliente → Atención → Calidad | Problema (calidad, entrega, factura) | Registrar, clasificar, asignar, responder | `Case` (+ lote) | **CRM → QMS** (calidad) / ERP (factura) | E24 | Fuerte |
| 15 | Recompra | Ventas / cliente | Consumo periódico | Nueva oportunidad tipo recompra | `Opportunity(type=recompra)` | — | E11 | Fuerte |

### 4.2 Variante: fórmula personalizada (E06)

Lead → requerimiento especial (sabor, aplicación, especificación) → **desarrollo de fórmula** (Desarrollo/Calidad) → **muestra enviada** → **muestra aprobada / rechazada** (iteración) → cotización → pedido.
Datos generados: brief de requerimiento, versión de muestra, retroalimentación del cliente. La fórmula (receta) **no** vive en el CRM.

### 4.3 Handoffs, automatizaciones y cuellos de botella potenciales (INFERIDOS)

- **Buzón único** (`administracion@`) → riesgo de que leads o reclamaciones se pierdan entre facturas y proveedores → clasificador + enrutamiento.
- **"Te contactaremos enseguida"** sin SLA medible → tarea automática de primer contacto con vencimiento en horas hábiles.
- **Leads bajo el mínimo (< 500 kg)** → consumen tiempo de ventas → marca automática y respuesta sugerida (no enviada).
- **Fórmulas** → muchas idas y vueltas sin registro → etapas explícitas de muestra.
- **Reclamaciones** → deben llegar a Calidad con lote; sin lote no hay trazabilidad → campo obligatorio para cerrar el caso.
- **Recompra** → oportunidad perdida si nadie mide la frecuencia de compra → P1: alerta de "cliente sin pedido en N días".

### 4.4 Partes DESCONOCIDAS (requieren validación interna)

Tamaño de la plantilla; quién responde hoy los formularios; si existe ERP/sistema contable (y cuál); política de precios y aprobaciones; condiciones de crédito; si la entrega es propia o tercerizada; lista real de productos y sectores del formulario; volumen de correos diario; si ya usan alguna hoja de cálculo o CRM; manejo actual de WhatsApp.

---

## 5. Salesforce como referencia conceptual

Fuente: https://www.salesforce.com/mx/crm/what-is-crm/ (consultado 21-sep-2026). Citas textuales cortas.

| PRINCIPIO_SALESFORCE | NECESIDAD_LA_HUERTA | FUNCIÓN_CRM (MVP) |
|---|---|---|
| "gestionar todas las interacciones… con los clientes actuales y potenciales" | Leads de 4 canales hoy dispersos (E13–E15) | `Lead` + `Activity` con `channel` |
| Gestión de contactos ("almacenar información de contacto") | Contactos por empresa; compras B2B con varios interlocutores | `Contact` N:1 `Account` |
| Cuentas con historial | Clientes por volumen y recurrentes (E02, E11) | Vista de cuenta 360 (contactos, oportunidades, cotizaciones, pedidos-ref, casos, correos) |
| Prospectos ("registrar cada interacción… con un prospecto") | Formularios web y catálogo (E14, E15) | Captura + deduplicación + calificación |
| Oportunidades ("ruta clara desde las preguntas iniciales hasta las ventas") | Cotizar pedidos; fórmulas especiales (E06) | `Opportunity` con pipeline y subflujo de fórmula |
| Pipeline ("vista clara de su cartera… pronósticos") | Priorizar volumen | Kanban por etapa + valor/kg estimado |
| Servicio al cliente ("historial completo de un cliente") | Reclamaciones FSSC con lote (E24) | `Case` ligado a cuenta y lote |
| Marketing basado en datos | Medir pauta Google/Meta/LinkedIn (E20) | `Lead.source` + `campaign` |
| Automatización ("automatizan la captura de datos") | Buzón compartido (E17) | Clasificador + extracción + tareas sugeridas |
| Reportes y análisis | Dirección necesita visibilidad | Dashboard mínimo |
| Integración entre departamentos ("une a tus equipos") | Handoffs Ventas↔Calidad↔Admin↔Almacén | Enrutamiento por categoría/rol + `IntegrationEvent` |
| Vista 360 | Una cuenta = un lugar | Página de cuenta |
| "única fuente de verdad" | Evitar duplicar lo operativo | CRM maestro de clientes; **referencias** a ERP/WMS/QMS |
| "integrarlos sin problemas en un solo CRM" | ERP/WMS/QMS futuros | Capa de integración con adaptadores + outbox |
| Escalabilidad ("agregar más a medida que tu negocio crezca") | Empresa en crecimiento | Módulos desacoplados, SQL portable a PostgreSQL |

Lo que **no** copiamos: objetos genéricos de Salesforce sin evidencia (campañas complejas, forecasting por territorio, portales, CPQ completo).

---

## 6. Delimitación CRM vs sistemas operativos

| Proceso | CRM | ERP | WMS | QMS | Otro | Integración necesaria |
|---|---|---|---|---|---|---|
| Captura de leads (web, WhatsApp, tel., correo) | **Maestro** | — | — | — | Web / proveedor de correo | Webhook de formulario → API CRM; Gmail API (lectura) |
| Cuentas y contactos (datos comerciales) | **Maestro** | Copia (cliente fiscal) | — | — | — | CRM → ERP al ganar (alta de cliente) |
| Datos fiscales / crédito | Referencia (bandera) | **Maestro** | — | — | Contabilidad | ERP → CRM (estado de crédito) |
| Oportunidades / pipeline | **Maestro** | — | — | — | — | — |
| Cotizaciones | **Maestro** (documento comercial) | Precios de lista / costos | Disponibilidad | — | — | ERP → CRM (lista de precios) |
| Pedidos de venta | Referencia (`OrderReference`: folio, estado, fechas) | **Maestro** | — | — | — | ERP ↔ CRM (evento de estado) |
| Inventario / stock de seguridad | Solo consulta futura | Parcial | **Maestro** | — | — | WMS → CRM (disponibilidad, P2) |
| Molienda / acondicionamiento / empaque | — | MRP/Producción | Parcial | Registros | — | Ninguna en MVP |
| Lotes y trazabilidad | Referencia (`lot_reference` en caso) | Parcial | **Maestro** | Maestro de liberación | — | QMS/WMS → CRM (validar lote, P1) |
| Compras / importaciones / proveedores | Solo enrutar correo | **Maestro** | — | Aprobación de proveedores | Agente aduanal | Clasificador → bandeja de Compras |
| Fórmulas personalizadas | Seguimiento comercial (etapas, muestra) | Receta/BOM | — | Especificación | — | CRM → ERP/QMS (brief), P1 |
| Reclamaciones | **Maestro del caso con cliente** | Nota de crédito | — | **Maestro de investigación/CAPA** | — | CRM → QMS (abrir no conformidad) |
| Distribución / entrega | Referencia (estado, fecha) | Maestro | Embarque | — | Transportista | ERP/WMS → CRM |
| Facturación / cobranza | Referencia (bandera saldo vencido) | **Maestro** | — | — | SAT / CFDI | ERP → CRM |
| Marketing / campañas | Origen del lead, campaña | — | — | — | Google Ads / Meta / LinkedIn | UTM → CRM |
| Correo | Registro, clasificación, vínculo | — | — | — | Gmail/Workspace (DESCONOCIDO si usan Google) | Adaptador de proveedor de correo |
| Auditoría / privacidad | **Maestro** de su propia bitácora | — | — | — | — | — |
