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

### 2.1 Medición real (Iteraciones 8 a 11 de DECISIONES.md)

Una vez que el usuario consiguió una `ANTHROPIC_API_KEY` propia, se corrió
`agente/correr_corridas_reales.py` contra la API real (no una estimación).
El flujo hace **dos llamadas** por legajo: una con `tool_choice` forzado a
`evaluar_legajo`, otra con `output_config.format` para el JSON final —
`response.usage` de ambas llamadas, sumado. Esta es la corrida más
reciente (post Iteración 11 — esquema con `null` y `datos_faltantes`
agregados al prompt, lo que sumó algo de contexto a las 4 corridas):

| Legajo | Input tokens (real) | Output tokens (real) | Costo real (Haiku 4.5) |
|---|---|---|---|
| Perez | 11 311 | 606 | USD 0,014341 |
| Gonzalez | 11 765 | 659 | USD 0,015060 |
| Lopez | 12 975 | 959 | USD 0,017770 |
| **Total (3 legajos de negocio)** | **36 051** | **2 224** | **USD 0,047171** |
| **Promedio por legajo de negocio** | 12 017 | 741 | **USD 0,015724** |
| Martinez (caso de prueba "incompleto", no es un legajo de negocio) | 10 780 | 608 | USD 0,013820 |

Cada corrida completa (`corridas/*/runs/<timestamp>/`) queda archivada sin
sobrescribir la anterior (Iteración 11) — el historial completo de costos
por corrida, no solo el promedio, está en esas carpetas.

El costo sigue subiendo en cada iteración real (§2.2 tenía la estimación
original, ≈USD 0,0055; Iteración 8 midió USD 0,011174; esta corrida, USD
0,015724), y por la misma razón cada vez: más verificación real (comprobantes,
detección de atípicos, manejo de nulls) significa más contexto en el prompt.
Es un trade-off explícito y documentado, no un costo que se esconde: "gastar
más tokens" a cambio de "confiar menos en un dato que puede estar mal
cargado o incompleto" — y sigue siendo, en términos absolutos, un costo
irrelevante (ver §3).

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

| Modelo | Precio in/out (por MTok) | Costo real por legajo (12 017 in / 741 out) |
|---|---|---|
| **Claude Haiku 4.5** (elegido) | $1.00 / $5.00 | **USD 0,0157** |
| Claude Sonnet 5 | $2.00 / $10.00 | USD 0,0315 (2× más caro) |
| Claude Opus 5 | $5.00 / $25.00 | USD 0,0786 (5× más caro) |

Cálculo: `costo = (input_tokens/1e6)×precio_input + (output_tokens/1e6)×precio_output`.

## 3. Proyección de costo corriendo en serio

**Supuesto explícito** (no hay dato real de volumen de la empresa — se
declara acá para que quede a la vista, no escondido en una celda): tomamos
un escenario base de **20 legajos por semana** (una hipotecaria chica/
mediana), y un escenario alto de **200 legajos por semana** para mostrar que
la conclusión no cambia con el volumen.

Costo por legajo usado en la proyección: **USD 0,015724** (medición real
más reciente, §2.1 — no la estimación de §2.2). Este número ya incluye el
costo extra de la verificación contra comprobantes reales (Iteración 10) y
del manejo de datos faltantes (Iteración 11) — es el costo de la versión
del sistema que efectivamente se entrega, no la versión más barata y menos
verificada de la primera corrida.

| Escenario | Legajos/semana | Costo semanal (Haiku) | Costo anual (52 sem.) |
|---|---|---|---|
| Base | 20 | ≈ USD 0,31 | **≈ USD 16,35** |
| Alto | 200 | ≈ USD 3,14 | ≈ USD 163,53 |

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
