# Diagramas

Fuente versionable: `docs/diagrams/*.mmd` (Mermaid). Cada fuente se validó renderizándola con Mermaid 11 (21-sep-2026); los `.svg` se regeneran con el mismo motor. Los nombres coinciden con tablas y módulos del código.

Lucid: acceso **verificado** (búsqueda y creación funcionaron el 21-sep-2026). Documentos creados en la cuenta de Lucid de Erii (privados; sin compartir):

| # | Diagrama | Fuente | Lucid |
|---|---|---|---|
| 1 | System Context | `01_system_context.mmd` | https://lucid.app/lucidchart/2c5aced3-8242-4bdd-ae50-303094e821f4/edit |
| 2 | Organigrama inferido (no oficial) | `02_organigrama_inferido.mmd` | https://lucid.app/lucidchart/7814f937-827e-4a34-bb3b-bfeef14ae08e/edit (organigrama nativo) |
| 2b | Capability Map | `02b_capability_map.mmd` | https://lucid.app/lucidchart/98e99a47-bb96-40f7-bd3a-244a49a91b1f/edit |
| 3 | Customer Journey / proceso comercial | `03_customer_journey.mmd` | https://lucid.app/lucidchart/0091716b-3398-414d-9e27-f94a73d51291/edit |
| 4 | Arquitectura lógica | `04_arquitectura_logica.mmd` | https://lucid.app/lucidchart/da383116-a646-437d-a2ca-1be4df270d9f/edit |
| 5 | ERD | `05_erd.mmd` | https://lucid.app/lucidchart/86a5d54c-b661-4f99-98d2-3ee33d61f538/edit (ERD nativo, columnas principales) |
| 6 | Flujo del clasificador | `06_flujo_clasificador.mmd` | https://lucid.app/lucidchart/3ba25f31-15ab-4b1a-a315-0b0f86e39571/edit |
| 7 | Integration Map | `07_integration_map.mmd` | https://lucid.app/lucidchart/4bb212a7-b44c-4fa2-860d-5a1df7736ac6/edit |

Notas:
- La **fuente de verdad** es el Mermaid del repositorio (D-16). Si se edita en Lucid, actualizar el `.mmd`.
- El ERD de Lucid muestra las columnas principales; el modelo completo está en `app/models.py`.
- No se revisó visualmente el acomodo automático de Lucid; puede requerir ajuste manual de posiciones.
