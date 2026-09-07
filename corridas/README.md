# Corridas reales

Tres legajos reales, tomados de la carpeta de Google Drive **"Trabajo Final -
Creación agentes de IA"** (compartida por el usuario), subcarpetas:

- `Crédito 1 - Perez` → `01 - #1 Perez.xlsx`
- `Crédito 2 - Gonzalez` → `02 - #2 Gonzalez.xlsx`
- `Crédito 3 - Lopez` → `03 - #3 Lopez.xlsx`

Cada uno de esos Excel tiene una hoja "Resumen Carpeta" con los datos del
cliente y del crédito. Ese es el dato de entrada real de cada corrida.

## Cómo se ejecutaron estas 3 corridas (y por qué no vía `agente/legajo_agent.py`)

Esta entrega no tuvo acceso a una `ANTHROPIC_API_KEY` propia (ver
`DECISIONES.md`, Iteración 3). En vez de simular los resultados, las 3
corridas se ejecutaron de verdad, con el mismo contrato (mismo
`prompts/system_prompt.md`, mismo `prompts/user_prompt.md`, mismos dos
controles duros), pero con dos componentes reales distintos a
`legajo_agent.py`:

1. **Lectura del legajo (herramienta 1 — conector real)**: Claude, corriendo
   dentro de la sesión de Claude Code que construyó este repo, usó su
   conector MCP de Google Drive (`mcp__Google_Drive__search_files`) para
   leer el contenido real de cada Excel directamente de la carpeta
   compartida. El texto de `entrada.md` en cada corrida es el
   `contentSnippet` devuelto por esa llamada, sin editar.
2. **Cálculo de los controles (herramienta 2 — código determinista)**: los
   porcentajes de cada control se calcularon ejecutando
   `python agente/tools.py` de verdad (no a mano, no estimado por el LLM) —
   ver la salida real de esa ejecución más abajo.

La extracción de campos (nombre, jurisdicción, ingresos, etc.) y la redacción
de `observaciones`/`motivo` las hizo el mismo modelo (Claude) aplicando
literalmente las reglas de `prompts/system_prompt.md`, tal como lo haría
`legajo_agent.py` en producción con la API — la diferencia es el canal
(sesión de Claude Code vs. llamada a la API con una key propia), no el
contrato ni la lógica.

### Salida real de `python agente/tools.py` (las 3 corridas, corrida en esta entrega)

```
Perez -> ingreso promedio: 2707521.33
{
  "control_1_cuota_ingreso": {"valor_medido_pct": 27.3, "limite_pct": 40.0, "aprueba": true},
  "control_2_ltv": {"valor_medido_pct": 20.4, "limite_pct": 35.0, "aprueba": true},
  "resultado_final": "ok credito aprobado",
  "motivo": null
}

Gonzalez -> ingreso promedio: 2709944.17
{
  "control_1_cuota_ingreso": {"valor_medido_pct": 39.4, "limite_pct": 40.0, "aprueba": true},
  "control_2_ltv": {"valor_medido_pct": 27.5, "limite_pct": 35.0, "aprueba": true},
  "resultado_final": "ok credito aprobado",
  "motivo": null
}

Lopez -> ingreso promedio: 1702509.5
{
  "control_1_cuota_ingreso": {"valor_medido_pct": 43.2, "limite_pct": 40.0, "aprueba": false},
  "control_2_ltv": {"valor_medido_pct": 40.5, "limite_pct": 35.0, "aprueba": false},
  "resultado_final": "credito no aprobado",
  "motivo": "Relación cuota/ingreso de 43.2% supera el límite de 40%; LTV de 40.5% supera el límite de 35%"
}
```

Un tercero puede reconstruir exactamente estos números corriendo
`python agente/tools.py` (no requiere API key — son solo los dos controles
deterministas) y comparándolos contra los `entrada.md`/`salida.json` de cada
corrida.

## Fecha

Las 3 corridas se ejecutaron el **2026-09-07** (mismo día en que el usuario
conectó Google Drive y pidió avanzar con la consigna).
