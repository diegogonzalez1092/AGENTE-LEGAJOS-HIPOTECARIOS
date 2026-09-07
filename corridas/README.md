# Corridas reales

Tres legajos reales, tomados de la carpeta de Google Drive **"Trabajo Final -
Creación agentes de IA"** (compartida por el usuario), subcarpetas:

- `Crédito 1 - Perez` → `01 - #1 Perez.xlsx`
- `Crédito 2 - Gonzalez` → `02 - #2 Gonzalez.xlsx`
- `Crédito 3 - Lopez` → `03 - #3 Lopez.xlsx`

Más un cuarto caso, `corrida_04_incompleto`: un legajo **sintético**
(construido a mano, no viene de Drive) para probar el manejo de datos
faltantes — ver Iteración 11 en `DECISIONES.md`. No entra al Excel maestro.

Cada uno de los 3 Excel reales tiene una hoja "Resumen Carpeta" con los
datos del cliente y del crédito. Ese es el dato de entrada real de cada
corrida.

Cada carpeta de corrida trae los tres artefactos que pide la consigna, cada
uno en su propio archivo:

- `entrada.md` — el dato de entrada real (texto crudo del legajo + qué
  herramienta lo trajo).
- `salida.json` — el resultado estructurado de la corrida **más reciente**.
- `fecha.txt` — fecha/hora UTC de la corrida más reciente.
- `metadata.json` — extra: canal de ejecución, modelo, tokens y costo de
  la corrida más reciente.
- `runs/<timestamp>/` — **el historial completo, sin sobrescribir**: cada
  vez que se corre `agente/correr_corridas_reales.py` se agrega una carpeta
  nueva acá con su propio `salida.json`/`metadata.json`/`fecha.txt`. Los
  4 archivos de arriba son solo un espejo de la carpeta de `runs/` más
  reciente, para que el resto del repo no tenga que saber el timestamp
  exacto (ver Iteración 11 en `DECISIONES.md` — sugerencia del agente
  evaluador del grupo).

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
verificación cruzada, y se volvió a correr contra la API.

**Etapa 4 (Iteración 11)** — se probó el agente evaluador del parcial del
grupo (`evaluador-grupo-33`) contra este repo: 96/100, con 3 sugerencias.
Se implementaron las tres: cliente real de Google Drive
(`agente/drive_client.py`), esquema de salida compatible con `null` para
legajos incompletos (con el cuarto caso de prueba,
`corrida_04_incompleto`), y corridas versionadas en `runs/` en vez de
sobrescribirse. Esta es la etapa que dejó la estructura de carpetas que ves
ahora — con historial completo de corridas, no solo la última.

### Cómo reproducir estas corridas

```bash
pip install -r agente/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python agente/correr_corridas_reales.py
```

Lee `corridas/*/entrada.md`, corre el agente real contra la API para cada
legajo (los 3 de negocio + el caso de prueba incompleto), guarda cada
corrida en `corridas/<caso>/runs/<timestamp>/` sin tocar corridas
anteriores, actualiza el espejo de "última corrida" a nivel
`corridas/<caso>/`, y regenera `output/legajos_maestro.xlsx` (solo con los
3 legajos de negocio). No requiere acceso a Google Drive — el texto de
entrada ya está guardado en este repo.

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

## Costo real medido (`response.usage`, modelo `claude-haiku-4-5`, corrida más reciente)

| Legajo | Input tokens | Output tokens | Costo |
|---|---|---|---|
| Perez | 11 311 | 606 | USD 0,014341 |
| Gonzalez | 11 765 | 659 | USD 0,015060 |
| Lopez | 12 975 | 959 | USD 0,017770 |
| **Total (3 legajos de negocio)** | **36 051** | **2 224** | **USD 0,047171** |
| Martinez (caso de prueba incompleto) | 10 780 | 608 | USD 0,013820 |

Ver `ANALISIS_ECONOMICO.md` para la proyección semanal/anual con este dato.

## Fecha

Etapa 1: 2026-09-07 (lectura de Drive). Etapa 2 (fix del promedio, Iteración
9): 2026-09-07. Etapa 3 (verificación de comprobantes y detección de
atípicos, Iteración 10): 2026-09-07. Etapa 4 (cliente de Drive, esquema con
null, corridas versionadas, Iteración 11): 2026-09-07 — mismo día las
cuatro.
