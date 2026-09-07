# Corridas reales

Tres legajos reales, tomados de la carpeta de Google Drive **"Trabajo Final -
Creación agentes de IA"** (compartida por el usuario), subcarpetas:

- `Crédito 1 - Perez` → `01 - #1 Perez.xlsx`
- `Crédito 2 - Gonzalez` → `02 - #2 Gonzalez.xlsx`
- `Crédito 3 - Lopez` → `03 - #3 Lopez.xlsx`

Cada uno de esos Excel tiene una hoja "Resumen Carpeta" con los datos del
cliente y del crédito. Ese es el dato de entrada real de cada corrida.

Cada carpeta de corrida trae los tres artefactos que pide la consigna, cada
uno en su propio archivo:

- `entrada.md` — el dato de entrada real (texto crudo del legajo + qué
  herramienta lo trajo).
- `salida.json` — el resultado estructurado real del agente.
- `fecha.txt` — fecha/hora UTC exacta de la corrida (también repetida
  dentro de `metadata.json` y en el encabezado de `entrada.md`, para que no
  dependa de un solo archivo).
- `metadata.json` — extra: canal de ejecución, modelo, tokens y costo real.

## Cómo se generó esta evidencia (dos etapas, documentadas en DECISIONES.md)

**Etapa 1 (Iteración 3)** — sin `ANTHROPIC_API_KEY` propia todavía: la
lectura del legajo se hizo con el conector real de Google Drive de la sesión
de Claude Code que construyó este repo, y el cálculo de los controles
corriendo de verdad `python agente/tools.py`. Esa primera versión de
`salida.json`/`metadata.json` quedó reemplazada por la Etapa 2.

**Etapa 2 (Iteraciones 8 y 9)** — el usuario consiguió una API key propia.
`agente/correr_corridas_reales.py` corrió el agente real (`legajo_agent.py`)
contra la API de Anthropic para los 3 legajos, usando exactamente el texto
de `entrada.md` ya capturado en la Etapa 1 (sin volver a tocar Drive). La
primera corrida de esta etapa encontró un bug real (el modelo promediaba mal
los ingresos mensuales — ver Iteración 9), que se corrigió en
`agente/tools.py`, y se volvió a correr.

**Etapa 3 (Iteración 10)** — el usuario, mirando el Excel entregado, notó
que el ingreso de agosto de Lopez no coincidía con los comprobantes reales.
Se verificó contra la carpeta "Ingresos" de los 3 legajos en Drive (solo
Lopez tenía discrepancia), se agregó a `agente/tools.py` la detección de
meses de ingreso atípicos, se actualizó `entrada.md` de los 3 legajos con la
verificación cruzada, y se volvió a correr contra la API. **`salida.json`,
`fecha.txt` y `metadata.json` de cada carpeta son el resultado de esta
tercera corrida**, con `usage` y costo reales de `response.usage` (no
estimados) y ya con la corrección de datos de Lopez incorporada.

### Cómo reproducir estas 3 corridas

```bash
pip install -r agente/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python agente/correr_corridas_reales.py
```

Lee `corridas/*/entrada.md`, corre el agente real contra la API para cada
legajo, sobrescribe `salida.json`/`metadata.json` con el resultado y el
costo real, y regenera `output/legajos_maestro.xlsx`. No requiere acceso a
Google Drive — el texto de entrada ya está guardado en este repo.

Para verificar sólo los dos controles financieros (sin API key, en
segundos):

```bash
python agente/tools.py
```

## Resultado final (verificado tres veces: comprobantes reales, cálculo determinista standalone, y el LLM contra la API real)

| Legajo | Ingreso mensual usado | Control 1 (cuota/ingreso) | Control 2 (LTV) | Resultado |
|---|---|---|---|---|
| Perez | Comprobantes reales (recibo de sueldo) | 27,2–27,3% — OK | 20,4% — OK | ok crédito aprobado |
| Gonzalez | Comprobantes reales (facturación), coinciden exacto con el resumen | 39,4% — OK (margen ajustado) | 27,5% — OK | ok crédito aprobado |
| Lopez | Comprobantes reales (facturación) — **no** el Resumen Carpeta, que tenía 2 meses mal cargados | 41,5% — NO CUMPLE | 40,5% — NO CUMPLE | crédito no aprobado, **+ advertencia de ingreso atípico en agosto** (6,4x la mediana) |

## Costo real medido (`response.usage`, modelo `claude-haiku-4-5`, corrida final con verificación de comprobantes)

| Legajo | Input tokens | Output tokens | Costo |
|---|---|---|---|
| Perez | 10 307 | 471 | USD 0,012662 |
| Gonzalez | 10 761 | 524 | USD 0,013381 |
| Lopez | 11 971 | 619 | USD 0,015066 |
| **Total** | **33 039** | **1 614** | **USD 0,041109** |

Ver `ANALISIS_ECONOMICO.md` para la proyección semanal/anual con este dato.

## Fecha

Etapa 1: 2026-09-07 (lectura de Drive). Etapa 2 (fix del promedio, Iteración
9): 2026-09-07. Etapa 3 (verificación de comprobantes y detección de
atípicos, Iteración 10): 2026-09-07 — mismo día las tres.
