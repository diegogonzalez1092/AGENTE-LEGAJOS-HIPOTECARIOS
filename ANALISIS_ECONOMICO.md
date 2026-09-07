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

### 2.1 Medición real (Iteración 8 y 9 de DECISIONES.md)

Una vez que el usuario consiguió una `ANTHROPIC_API_KEY` propia, se corrió
`agente/correr_corridas_reales.py` contra la API real (no una estimación).
El flujo hace **dos llamadas** por legajo: una con `tool_choice` forzado a
`evaluar_legajo`, otra con `output_config.format` para el JSON final —
`response.usage` de ambas llamadas, sumado:

| Legajo | Input tokens (real) | Output tokens (real) | Costo real (Haiku 4.5) |
|---|---|---|---|
| Perez | 8 524 | 478 | USD 0,010914 |
| Gonzalez | 8 759 | 497 | USD 0,011244 |
| Lopez | 8 650 | 543 | USD 0,011365 |
| **Total (3 corridas)** | **25 933** | **1 518** | **USD 0,033523** |
| **Promedio por corrida** | 8 644 | 506 | **USD 0,011174** |

Esto es ≈2× la primera estimación por caracteres (§2.2, dejada abajo tal
cual se hizo, sin corregir después de tener el dato real — ver
`DECISIONES.md` sobre por qué documentar el error de estimación es parte de
la nota). La diferencia se explica por dos motivos concretos que solo se ven
midiendo de verdad: el `input_schema` completo de la herramienta (que la API
factura como parte del prompt) y el `system_prompt.md` completo se mandan en
**las dos** llamadas, no en una sola; y las `observaciones` que redacta el
modelo terminaron siendo más largas de lo estimado (explican volatilidad de
ingresos, documentación faltante, etc.).

### 2.2 Estimación original (antes de tener API key — dejada como referencia)

Método: se midió el tamaño en caracteres de `prompts/system_prompt.md` +
`corridas/*/entrada.md` + el esquema de la herramienta, y se convirtió a
tokens con la aproximación de ~4 caracteres por token (sin poder validarla
con `client.messages.count_tokens` en ese momento).

| Legajo | Caracteres de entrada (system+legajo) | Input tokens (≈, 2 llamadas) | Output tokens (≈) |
|---|---|---|---|
| Perez | 7 334 | ≈ 4 000 | ≈ 180 |
| Gonzalez | 7 557 | ≈ 4 100 | ≈ 210 |
| Lopez | 7 571 | ≈ 4 100 | ≈ 300 |

Estimación resultante: ≈USD 0,0055 por legajo — **subestimada por ~2×**
frente a la medición real de §2.1.

### 2.3 Comparación de modelos (con el perfil de tokens real, §2.1)

| Modelo | Precio in/out (por MTok) | Costo real por legajo (8 644 in / 506 out) |
|---|---|---|
| **Claude Haiku 4.5** (elegido) | $1.00 / $5.00 | **USD 0,0112** |
| Claude Sonnet 5 | $2.00 / $10.00 | USD 0,0224 (2× más caro) |
| Claude Opus 5 | $5.00 / $25.00 | USD 0,0559 (5× más caro) |

Cálculo: `costo = (input_tokens/1e6)×precio_input + (output_tokens/1e6)×precio_output`.

## 3. Proyección de costo corriendo en serio

**Supuesto explícito** (no hay dato real de volumen de la empresa — se
declara acá para que quede a la vista, no escondido en una celda): tomamos
un escenario base de **20 legajos por semana** (una hipotecaria chica/
mediana), y un escenario alto de **200 legajos por semana** para mostrar que
la conclusión no cambia con el volumen.

Costo por legajo usado en la proyección: **USD 0,011174** (medición real,
§2.1 — no la estimación de §2.2).

| Escenario | Legajos/semana | Costo semanal (Haiku) | Costo anual (52 sem.) |
|---|---|---|---|
| Base | 20 | ≈ USD 0,22 | **≈ USD 11,62** |
| Alto | 200 | ≈ USD 2,23 | ≈ USD 116,21 |

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
