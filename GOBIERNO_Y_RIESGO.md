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
| Google Drive (carpeta de legajos) | Lectura únicamente (`search_files`, `read_file_content`, `download_file_content`) | Solo la carpeta del legajo que se le indica explícitamente en cada corrida. No lista ni navega el Drive completo del usuario, no escribe ni borra archivos ahí. |
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
| **Aritmética incorrecta del LLM** | Los controles financieros determinan si a alguien se le aprueba o rechaza un crédito hipotecario — un error de cálculo tiene impacto legal/económico real | El cálculo NUNCA lo hace el LLM en texto libre: siempre pasa por `agente/tools.py::evaluar_legajo`, código determinista y testeable (L0) |
| **Ingresos volátiles mal promediados** (caso Lopez: de ARS 70.000 a ARS 6.000.000 en 6 meses) | Promediar sin más un ingreso así puede ocultar el riesgo real | El agente está instruido (`system_prompt.md`, regla 4) a marcar explícitamente alta volatilidad en `observaciones`, aunque el promedio pase los controles |
| **Legajo incompleto** (falta valor de propiedad, cuota, etc.) | No ocurrió en las 3 corridas reales, pero está previsto | El agente no inventa el dato faltante: devuelve `null` y lo señala (ver variante en `prompts/user_prompt.md`) |
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
