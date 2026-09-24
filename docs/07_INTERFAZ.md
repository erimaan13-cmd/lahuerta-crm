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

## Pendiente

- Densidad de las tablas largas en celular (el pipeline por etapa queda muy alto).
- Modo oscuro, si el cliente lo pide.
- Revisión de contraste con herramienta automática al desplegar en un dominio real.
