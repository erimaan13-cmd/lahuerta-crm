# 07 · Interfaz: navegación, sistema visual y accesibilidad

Septiembre 2026. Rediseño de la interfaz después de auditar el sistema en pantalla real
(capturas a 390 px y 1280 px). El problema no era el estilo: era la navegación.

## Qué estaba mal (VERIFICADO en capturas, 24-sep-2026)

| Hallazgo | Efecto |
|---|---|
| 17 enlaces en una barra superior que se partía en 7 renglones en celular | el menú ocupaba el primer tercio de la pantalla |
| Todos los módulos al mismo nivel | sin jerarquía; demasiadas opciones simultáneas (ley de Hick) |
| Tarjetas de cifras a ancho completo | 800 px de desplazamiento para ver seis números |
| Tablas anchas cortadas | columnas invisibles, sin señal de que se puede deslizar |
| Menú no fijo, foco de teclado invisible, toques < 44 px | navegación incómoda y poco accesible |

## Qué se hizo

**Navegación.** Una sola lista de enlaces agrupada en cuatro bloques —Comercial, Operación,
Administración, Sistema— que el CSS convierte en barra lateral fija (≥1024 px) o en menú deslizante
(<1024 px). Cada rol ve solo sus módulos, así nadie enfrenta 17 opciones. En celular, una barra
inferior con los cuatro accesos más usados: Tablero, Avisos, Buscar y Menú.

**Tablas legibles en celular.** Un script copia el encabezado de cada columna a su celda
(`data-label`) y el CSS convierte cada fila en una ficha "Producto: Orégano". Funciona en las
30 pantallas sin tocar ninguna plantilla.

**Sistema visual.** `app/static/app.css`: paleta de la marca validada por el cliente (café, dorado,
crema) sobre una escala de neutros, y variables para espacio, radios, sombras y tipografía. Iconos
de línea propios en SVG, con el mismo trazo en todo el menú.

**Accesibilidad (WCAG 2.1 AA).** Enlace "saltar al contenido", foco visible de 3 px en todo
elemento, controles de 44 px, menú deslizante operable con teclado (Esc cierra y el foco regresa al
botón), `aria-current` en la página activa, y `prefers-reduced-motion` respetado.

## Decisiones que conviene conocer

- **Sin skeletons decorativos.** El servidor entrega la página ya armada: un skeleton aparecería y
  desaparecería en el mismo instante. En su lugar hay una barra de progreso al navegar. Si algún día
  se cargan tablas por separado con JavaScript, ahí sí tendrán sentido.
- **Sin shadcn/ui ni Tailwind.** Son para React; la interfaz es HTML generado por Python. Se tomaron
  sus criterios (escala, radios, anillo de foco, variantes de botón) y se escribieron en CSS plano:
  mismo resultado sin reescribir la aplicación ni sumar Node al despliegue.
- **Sin copiar plantillas de terceros.** Del catálogo revisado se tomó el patrón general
  (barra lateral + barra superior + tarjetas), que es de uso común, no el diseño de ninguna plantilla.

## Iteración 6 · auditoría con capturas reales del cliente (25-sep-2026)

Erick revisó el sistema en su iPhone a través del túnel y envió capturas señaladas. Se corrigió:

| Señalamiento | Corrección | Alcance |
|---|---|---|
| Correos y dominios cortados por la derecha | El contenido de cada celda se agrupa en `div.valor` y parte lo que no cabe; el rótulo baja a 30 % | Todas las fichas de celular (D-48) |
| El desplegable de Usuario se salía del recuadro y "zoomeaba" la página | `min-width: 0` en las etiquetas: ningún campo excede su contenedor | Todos los formularios (D-49) |
| "Revisar ahora" y "Crear orden en borrador" con el texto a un costado | Clase `.hint`: el texto va debajo, en su renglón | Avisos, Abastecimiento, Leads, Cuentas |
| Controles amontonados (rol + Cambiar, contraseña + Restablecer, silenciar) | `form.inline` pasa a `inline-flex` con separación; celdas con varias acciones usan `.acciones` | Usuarios, Avisos |
| Chips de filtro en minúscula, con guion bajo y sin contraste | Componente `.fchip` con etiqueta legible y estado activo en color de marca | Cuentas |
| 18 chips de filtro en Correos, y filtros de Tareas sin prioridad | Desplegables que se aplican al elegir (D-51) | Correos, Tareas |
| "Ingerir buzón", "Subir .eml" sin significado | Renombrados y con nota de una línea; el detalle va a la documentación (D-53) | Correos |
| Historial: selectores sin relación entre sí, IP y detalle ilegibles | Área reduce la lista de usuarios (D-52), técnico a "Búsqueda avanzada", IP solo en monitor (D-54) | Historial |
| Lista de oportunidades muy larga | Sección plegable con filtro por etapa | Tablero |
| "Sin tareas." con el rótulo TAREA al lado | Las celdas que abarcan la fila ya no reciben rótulo | Todas las tablas |

Verificación: sin desbordamiento horizontal en las ocho pantallas revisadas, a 390 px y a 1280 px,
con 233 pruebas en verde.

**Regla que quedó de esta iteración:** lo que necesita explicación se documenta en
`docs/08_GUION_DOCUMENTACION.md` (guía de uso, video y diagrama), no se imprime en pantalla.

## Pendiente

- Aplicar el mismo repaso a las pantallas de operación (inventario, mantenimiento, RRHH), que
  todavía no se revisaron con capturas del cliente.
- Modo oscuro, si el cliente lo pide.
- Revisión de contraste con herramienta automática al desplegar en un dominio real.
