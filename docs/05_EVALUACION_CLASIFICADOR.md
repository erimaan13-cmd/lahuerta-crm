# 05 · Evaluación del clasificador (iteración 2)

**Conclusión:** medido con correos escritos por un tercero que nunca vio las reglas, el clasificador **v1.1.1** acierta **75 %** (antes 53 %). De lo que decide solo, acierta **87 %** (antes 70 %). El 89 % reportado en la iteración 1 era optimista: salió de los mismos 18 correos con los que se ajustaron las reglas.

## Método

| Corpus | Correos | Quién lo redactó | Uso | Estado |
|---|---|---|---|---|
| `dev.json` | 96 (8 por categoría) | Subagente sin acceso al código ni a las reglas | **Ajuste de reglas** | Libre |
| `test_holdout.json` | 66 | Claude (autor de las reglas), antes de ajustar | Prueba | Congelado (SHA-256) |
| `test_independiente.json` | 72 (6 por categoría) | Otro subagente sin acceso al código ni a las reglas | **Prueba principal** | Congelado (SHA-256) |

- Guía de etiquetado común: `data/eval/GUIA_ETIQUETADO.md`. Incluye desempate para correos mixtos.
- Los conjuntos de prueba se congelaron **antes** de modificar reglas (commits `019c903` y `7cf5e7d`; las reglas cambian después, en `8246689`). `scripts/eval_corpus.py` verifica los hashes y se niega a correr si alguien los edita.
- Las reglas solo se ajustaron mirando `dev.json`. Los conjuntos de prueba se evaluaron una vez.
- Tras esa evaluación se corrigió un **defecto de código** hallado en ella: "S.A. de C.V." activaba la regla de currículum. Se reporta aparte como post-hoc. **No** se hizo ningún otro ajuste con los conjuntos de prueba.
- Reproducir: `python -m scripts.eval_corpus dev holdout independiente --sweep -v`.

## Resultados

| Versión | Corpus | Exactitud | Cobertura automática | Exactitud entre auto | Errores sin revisión |
|---|---|---|---|---|---|
| rules-1.0 (MVP) | dev | 56.2 % | 56.2 % | 68.5 % | 17 / 96 |
| rules-1.0 (MVP) | holdout (autor) | 59.1 % | 62.1 % | 70.7 % | 12 / 66 |
| rules-1.0 (MVP) | **independiente** | **52.8 %** | 51.4 % | **70.3 %** | 11 / 72 |
| rules-1.1 | dev *(ajustado aquí)* | 99.0 % | 70.8 % | 100 % | 0 / 96 |
| rules-1.1 | holdout (autor) | 98.5 % | 72.7 % | 100 % | 0 / 66 |
| rules-1.1 | **independiente** (evaluación única) | **75.0 %** | 62.5 % | **88.9 %** | 5 / 72 |
| rules-1.1.1 | **independiente** (post-hoc, tras corregir el defecto) | **75.0 %** | 63.9 % | **87.0 %** | 6 / 72 |

**Cómo leerlo (INFERIDO):**
- dev y holdout están inflados: dev por ajuste directo y holdout por sesgo de autor (quien escribe las reglas escribe con su mismo vocabulario). **La cifra que vale es la del corpus independiente.**
- **Cobertura automática** = correos que no pasan por Needs Review. Hoy **2 de cada 3** correos llegan clasificados; el resto los revisa una persona.
- **Errores sin revisión** = sugerencias equivocadas que no pasaron por Needs Review. No causan daño automático (D-12: nada se aplica sin clic humano), pero una persona puede aceptarlas sin leer con cuidado.

### Por categoría (independiente, v1.1.1)

| Categoría | Precisión | Recall | Lectura |
|---|---|---|---|
| DOCUMENTACION_CALIDAD, FORMULA_PERSONALIZADA | 100 % | 100 % | Vocabulario técnico estable |
| SEGUIMIENTO_COMERCIAL | 75 % | 100 % | Absorbe algunos pedidos que responden a una cotización |
| SOLICITUD_COTIZACION | 71 % | 83 % | Ofertas de proveedores parecen cotizaciones |
| ADMIN_FACTURACION | 60 % | 100 % | Atrae reclamaciones y spam que mencionan "factura" |
| CALIDAD_RECLAMACION | 100 % | 50 % | Faltan expresiones coloquiales ("viene quebrado", "puro polvo") |
| PEDIDO | 100 % | 50 % | Listas sin verbo de pedido y "mándenme lo mismo" |
| LEAD_NUEVO | 100 % | 33 % | Primer contacto sin palabras clave (el mayor hueco) |
| OTRO | 38 % | 100 % | Recoge lo que no reconoce: por diseño siempre va a revisión |

### Barrido de umbral (independiente)

| Umbral | Cobertura | Exactitud auto | Errores sin revisión |
|---|---|---|---|
| 0.60 (actual) | 62 % | 89 % | 5 |
| 0.70 | 51 % | 92 % | 3 |
| 0.80 | 36 % | 96 % | 1 |

Decisión D-18: se mantiene **0.60**. Un error "auto" solo produce una sugerencia equivocada que una persona debe aprobar. Si La Huerta prefiere menos errores y más revisión manual, basta con `CRM_CLASSIFIER_THRESHOLD=0.70`.

## Cambios de reglas (rules-1.0 → 1.1.1)

- Expresiones indirectas: "¿a cómo…?", "en cuánto nos dejarían", "mándenme lo mismo", "surtan", "sigo esperando la propuesta", "sabe diferente", "costales rotos", etc.
- Reglas en inglés para cotización, pedido, calidad, entrega, seguimiento, fórmula, spam y proveedor.
- Reglas propias de OTRO: vacantes, donativos, visitas escolares, respuestas automáticas y felicitaciones.
- Detección de phishing (cuentas suspendidas, paquetes retenidos, buzón lleno).
- **Prioridad para correos mixtos** (`PRIORITY_ABSORB`): calidad > pedido > entrega > facturación. Además, el seguimiento absorbe la cotización.
- Un proveedor conocido siempre puntúa como proveedor, aunque hable de facturas o precios.

## Pendiente (siguiente iteración del clasificador)

1. Recall de LEAD_NUEVO, PEDIDO y CALIDAD con lenguaje coloquial.
2. Aplicar por completo el desempate PEDIDO > SEGUIMIENTO: "autorizado, surtan…" en respuesta a una cotización.
3. Spam que imita facturas electrónicas (SAT/CFDI).
4. **Con cualquier ajuste nuevo, redactar otro corpus independiente.** El actual ya quedó "visto" y deja de ser prueba limpia.
5. Con correos reales, repetir la medición: es la única cifra definitiva (PENDIENTE: no hay acceso).
