# Análisis económico

## 1. Elección de modelo

El criterio del curso es **el modelo más chico que hace bien la tarea**. La
tarea de este agente es:

1. Extraer ~10 campos numéricos/texto de un resumen de legajo de formato
   irregular pero acotado (una sola hoja de cálculo, siempre la misma
   estructura de negocio).
2. Llamar a una herramienta con esos números (la aritmética la hace código
   Python determinista, no el modelo — ver `agente/tools.py` y
   `GOBIERNO_Y_RIESGO.md`).
3. Completar un JSON de salida con un esquema fijo.

No hay razonamiento multi-paso largo, no hay ambigüedad de dominio (las
reglas de negocio son dos umbrales fijos), y el paso más propenso a error
(la aritmética) está deliberadamente sacado del modelo. Este es exactamente
el perfil de tarea para el que un modelo chico basta.

**Elegimos `claude-haiku-4-5`** ($1.00 / $5.00 por millón de tokens de
entrada/salida) en vez de `claude-sonnet-5` ($2.00 / $10.00) o
`claude-opus-5` ($5.00 / $25.00). Se comparan los tres más abajo para dejar
la elección justificada con números, no solo con la regla general.

## 2. Costo por corrida

Método de estimación (no tuvimos `ANTHROPIC_API_KEY` propia para medir con
`client.messages.count_tokens` — ver `DECISIONES.md`, Iteración 3): se midió
el tamaño real en caracteres de `prompts/system_prompt.md` +
`corridas/*/entrada.md` + el esquema de la herramienta `evaluar_legajo`, y se
convirtió a tokens con la aproximación estándar de ~4 caracteres por token.
El flujo real de producción (`agente/legajo_agent.py`) hace **dos llamadas**
a la API por legajo: una donde el modelo llama a la herramienta
`evaluar_legajo`, y otra donde devuelve el JSON final ya con el resultado de
la herramienta adentro del historial — por eso el input efectivo es mayor
que un solo prompt.

| Legajo | Caracteres de entrada (system+legajo) | Input tokens (≈, 2 llamadas) | Output tokens (≈) |
|---|---|---|---|
| Perez | 7 334 | ≈ 4 000 | ≈ 180 |
| Gonzalez | 7 557 | ≈ 4 100 | ≈ 210 |
| Lopez | 7 571 | ≈ 4 100 | ≈ 300 |

Tomamos **4 000 tokens de entrada y 300 de salida** como estimación
conservadora por legajo (redondeando hacia arriba).

| Modelo | Precio in/out (por MTok) | Costo estimado por legajo |
|---|---|---|
| **Claude Haiku 4.5** (elegido) | $1.00 / $5.00 | **≈ USD 0,0055** |
| Claude Sonnet 5 | $2.00 / $10.00 | ≈ USD 0,011 (2× más caro) |
| Claude Opus 5 | $5.00 / $25.00 | ≈ USD 0,0275 (5× más caro) |

Cálculo: `costo = (input_tokens/1e6)×precio_input + (output_tokens/1e6)×precio_output`.

## 3. Proyección de costo corriendo en serio

**Supuesto explícito** (no hay dato real de volumen de la empresa — se
declara acá para que quede a la vista, no escondido en una celda): tomamos
un escenario base de **20 legajos por semana** (una hipotecaria chica/
mediana), y un escenario alto de **200 legajos por semana** para mostrar que
la conclusión no cambia con el volumen.

| Escenario | Legajos/semana | Costo semanal (Haiku) | Costo anual (52 sem.) |
|---|---|---|---|
| Base | 20 | ≈ USD 0,11 | **≈ USD 5,72** |
| Alto | 200 | ≈ USD 1,10 | ≈ USD 57,20 |

**Conclusión**: el costo de inferencia es irrelevante frente al problema de
negocio que se está resolviendo (horas de analista revisando carpetas a
mano). El cuello de botella económico real no es el modelo — es el tiempo de
revisión humana en los puntos de supervisión L1/L2 (ver
`GOBIERNO_Y_RIESGO.md`), que este sistema no elimina a propósito.

## 4. Costo no cubierto por esta estimación

- Llamadas reales a Google Drive / lectura de archivos (sin costo de
  tokens, pero sí de cuota de API de Google).
- Reintentos por errores de formato del legajo (legajos incompletos,
  columnas corridas) — en producción convendría medir la tasa real de
  reintentos con `client.messages.count_tokens` y los logs de `response.usage`
  antes de proyectar a un año completo con más precisión que la de este
  documento.
