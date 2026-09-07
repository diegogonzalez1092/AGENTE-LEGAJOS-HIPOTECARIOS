# Gobierno y riesgo

## 0. Vocabulario de supervisión (L0–L4) usado en este documento

> Igual que con las "seis piezas" del contrato (ver
> `prompts/system_prompt.md`), no tuvimos acceso a la definición exacta de
> L0–L4 dada en clase. Definimos acá la escala que usamos, de menor a mayor
> intervención humana, para que quede explícita y auditable:

| Nivel | Nombre | Qué significa |
|---|---|---|
| **L0** | Automatización total | El agente actúa solo. No hay revisión humana previa ni posterior obligatoria. Reservado para pasos deterministas y verificables por código (no por criterio del LLM). |
| **L1** | Revisión posterior muestral | El agente actúa solo; un humano revisa una muestra de los resultados después, no antes de que tengan efecto. |
| **L2** | Propuesta con revisión previa | El agente arma la recomendación completa, pero un humano la revisa **antes** de que tenga cualquier efecto real (comunicación al cliente, instrumentación del crédito). |
| **L3** | Aprobación explícita por ítem | Un humano tiene que aprobar cada salida individual, uno por uno, antes de ejecutarla. |
| **L4** | Solo humano | El agente no actúa sobre este paso. A lo sumo, sugiere. |

## 1. Sistemas que toca el agente y con qué permisos

| Sistema | Acceso del agente | Alcance |
|---|---|---|
| Google Drive (carpeta de legajos) | Lectura únicamente. En las corridas de este repo, vía el conector MCP de Claude Code; en producción, vía `agente/drive_client.py` con una cuenta de servicio de Google Cloud scopeada a `drive.readonly` (ver DECISIONES.md, Iteración 11) | Solo la carpeta del legajo que se le indica explícitamente en cada corrida — la cuenta de servicio de producción solo debe tener compartida esa carpeta, no todo el Drive de la empresa (mínimo privilegio). No lista ni navega el Drive completo del usuario, no escribe ni borra archivos ahí. |
| Excel maestro de legajos (`output/legajos_maestro.xlsx`) | Lectura y escritura (agregar filas) | Nunca sobreescribe ni borra filas existentes — `agente/excel_writer.py` solo hace `append`. |
| API de Anthropic (Claude) | Llamadas de inferencia | Sin acceso a otros sistemas de la empresa (no hay integración con el core bancario, el BCRA, ni el sistema de notificación al cliente). |

El agente **no tiene acceso** a: el sistema donde Legales corre BCRA/Veraz/
Nosis (eso ya pasó en el paso anterior del circuito y llega como dato
aprobado), ningún canal de comunicación con el cliente, ni ningún sistema de
firma o desembolso. Esto es deliberado: es un analista financiero júnior de
lectura y cálculo, no un sistema con autoridad de decisión ni de contacto.

## 2. Qué puede salir mal y qué pasa cuando sale mal

| Riesgo | Ejemplo concreto (visto en las 3 corridas reales) | Mitigación |
|---|---|---|
| **Extracción incorrecta de un campo** por formato irregular del resumen | En los 3 legajos, el campo etiquetado "Reserva Propiedad" en realidad contenía el ingreso promedio del cliente (ver `DECISIONES.md`) — un agente menos cuidadoso podría haber usado el valor equivocado como reserva y no como ingreso | El agente indica en `observaciones` cualquier campo que tuvo que reconciliar por ambigüedad de formato; el humano revisor (L1/L2) lo ve antes de que la fila se dé por buena |
| **Aritmética incorrecta del LLM** | **Ocurrió de verdad, no es hipotético**: en la primera corrida contra la API real, el legajo Lopez debía rechazarse pero salió "ok credito" en el Control 1 porque el modelo promedió mal 6 meses de ingresos (ARS 2.038.609 calculado vs. ARS 1.702.510 real) antes de pasarle el número a la herramienta — ver `DECISIONES.md`, Iteración 9 | Se cerró el hueco de raíz: `evaluar_legajo` ahora recibe la lista cruda de ingresos y promedia *adentro* del código (L0), no antes. El LLM ya no hace ninguna cuenta, ni siquiera un promedio simple. Se volvió a correr contra la API real después del fix y los 3 resultados coincidieron exactamente con el cálculo determinista |
| **Ingresos volátiles mal promediados** (caso Lopez: de ARS 70.000 a ARS 1.654.750 en 6 meses) | Promediar sin más un ingreso así puede ocultar el riesgo real | El agente está instruido (`system_prompt.md`, regla 4) a marcar explícitamente alta volatilidad en `observaciones`, aunque el promedio pase los controles |
| **Ingreso mensual atípico tratado como recurrente sin más** — **ocurrió de verdad**: el usuario, mirando el Excel entregado, notó que el ingreso de agosto de Lopez (ARS 6.000.000 en el resumen) no coincidía con los comprobantes reales de la carpeta "Ingresos" (ARS 6.500.000), y que además ese mes es 6,4x la mediana de los otros 5 meses — un solo pago, al mismo cliente único del legajo, muy fuera de todo patrón normal | Se verificó contra la carpeta "Ingresos" y se confirmó la discrepancia solo en julio y agosto de este legajo (Perez y Gonzalez coinciden). Se agregó detección determinista de meses atípicos (`promediar_ingresos`, umbral 3× la mediana) que alimenta un campo `advertencias` obligatorio, y una regla explícita de priorizar comprobantes reales sobre el resumen cuando ambos están disponibles (ver `DECISIONES.md`, Iteración 10) |
| **Legajo incompleto** (falta valor de propiedad, cuota, etc.) | No ocurrió en las 3 corridas reales, pero está previsto | El agente no inventa el dato faltante: devuelve `null` y lo señala (ver variante en `prompts/user_prompt.md`) |
| **Uso del monto de crédito equivocado en el LTV** | En la primera corrida real, el modelo usó "Total Crédito (Fee incluido)" en vez de "Crédito Aprobado" para 2 de los 3 legajos, dando un LTV distinto al que ya viene precalculado en el propio Excel del legajo (ver `DECISIONES.md`, Iteración 9) — no cambió el resultado final en estos 3 casos, pero podría cambiarlo en un legajo con el LTV más cerca del límite | Regla explícita agregada en `system_prompt.md` y en la descripción de la tool: usar siempre "Crédito Aprobado" |
| **Legajo incompleto forzaba a inventar datos o a saltear el control** | Antes de la Iteración 11, `evaluar_legajo` tenía sus 4 parámetros obligatorios y `tool_choice` forzado — si faltaba un dato, no había ninguna forma de responder correctamente sin inventar un número o reabrir el riesgo de la Iteración 9 (dejar que el LLM decida no llamar a la herramienta) | La herramienta ahora acepta `null` en cualquier campo, sigue llamándose siempre, y es el código el que decide qué control se puede evaluar (`datos_faltantes`). Probado contra la API real con un legajo sintético sin valor de propiedad — ver `corridas/corrida_04_incompleto` |
| **Cliente de Drive de producción sin probar end-to-end** | `agente/drive_client.py` sigue la API oficial y compila sin errores, pero no se corrió contra una cuenta de servicio real en este entorno (no había credenciales disponibles) | No se afirma que "ya funciona en producción" — queda documentado como pendiente en `DECISIONES.md`, Iteración 11, y en el propio módulo. Antes de usarlo con legajos reales, correr al menos una vez contra una carpeta de prueba con una cuenta de servicio real y comparar el texto extraído contra `corridas/*/entrada.md` |
| **Alucinación de aprobación** | El agente podría, en teoría, redactar "crédito aprobado" sin haber llamado a la herramienta | El `resultado_final` que arma el agente es una **recomendación técnica**, nunca la aprobación real — ver punto 3 (quién firma) |
| **Uso del agente fuera de su alcance** (ej. que alguien le pida evaluar perfil crediticio o hablar con el cliente) | — | El system prompt fija explícitamente que el agente no evalúa riesgo reputacional ni tiene autoridad de comunicación (regla de rol) |

## 3. Puntos de supervisión humana (con el vocabulario L0–L4)

| Paso del proceso | Nivel | Quién revisa / firma |
|---|---|---|
| Lectura y extracción de datos del legajo (Drive → campos estructurados) | **L1** | Analista financiero revisa una muestra de legajos procesados por semana, no cada uno |
| Cálculo de los 2 controles financieros (código determinista, `tools.py`) | **L0** | Ninguna — es aritmética verificable por unit tests, no un juicio del LLM |
| Redacción de `observaciones` y `motivo` | **L1** | Analista financiero, revisión muestral |
| Fila volcada al Excel maestro con `resultado_final` (recomendación) | **L2** | **Gerente de Riesgo / Comité de Crédito** revisa y firma la recomendación antes de que continúe el circuito (instrumentación del crédito o comunicación al deudor) |
| Comunicación de la decisión al cliente y firma de documentación | **L4** | Siempre humano. El agente nunca notifica directamente al deudor ni firma nada — eso excede por completo su contrato |

**Quién firma la aprobación final**: el **Gerente de Riesgo** (o el Comité de
Crédito, según el monto), nunca el agente. La fila del Excel maestro es un
insumo de trabajo para esa firma, no una aprobación en sí misma — por eso
`resultado_final` dice literalmente "ok crédito **aprobado**" únicamente
como etiqueta del control técnico, pero el `system_prompt.md` (regla 2)
prohíbe explícitamente al agente tratar esa etiqueta como una aprobación
real.

## 4. Qué revisa un humano antes de confiar en una salida del agente

Checklist mínimo para el analista/Gerente de Riesgo antes de firmar,
derivado directamente de los riesgos de la sección 2:

1. ¿Los campos extraídos (ingresos, cuota, valor de propiedad) coinciden con
   los que aparecen en el Excel original del legajo? (chequeo de extracción)
2. ¿El `motivo`/`observaciones` menciona algo que cambie el criterio de
   negocio (volatilidad de ingresos, documentación faltante, controles al
   límite como el 39,4% de Gonzalez)?
3. ¿La categoría tributaria del cliente (relación de dependencia /
   monotributista / autónomo) tiene la documentación de acreditación de
   ingresos que exige la política de la empresa?
4. Re-ejecutar `python agente/tools.py` (o los `evaluar_legajo` puntuales) si
   hay cualquier duda sobre el cálculo — es determinista y reproducible en
   segundos, sin costo de API.
5. ¿Hay `advertencias` de meses de ingreso atípicos? Si las hay, no
   alcanza con que el crédito ya esté rechazado por otro motivo (como en
   Lopez) — hay que verificar el comprobante real de ese mes específico
   antes de dar por buena cualquier fila del Excel maestro, aprobada o no.
