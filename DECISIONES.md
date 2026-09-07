# DECISIONES.md — historia del proceso

## Iteración 0 — El pedido original no era este trabajo final

El usuario arrancó pidiendo automatizar la revisión de legajos de una
empresa de créditos hipotecarios (documento `Prompt_FInal_IA.docx`), con un
pedido concreto: armar un Excel maestro con 14 columnas fijas a partir de
legajos que viven en una carpeta de Google Drive. En esa primera vuelta se
entendió como un entregable de negocio suelto, y se preguntó por acceso a
Drive antes de construir nada.

## Iteración 1 — Apareció la consigna real: no es un Excel, es un trabajo final de la materia

El usuario subió un segundo documento (`trabajo_final.pdf`): la consigna del
trabajo final de "Programación de y con Agentes de IA" (MBA UCEMA). Ahí
cambió el alcance real del proyecto — no alcanza con producir el Excel, hace
falta un **sistema agéntico completo**, con: contrato escrito (system +
user prompt), al menos una herramienta/conector real, salida estructurada,
supervisión humana con vocabulario L0–L4, evidencia de 3 corridas reales,
formato de repo obligatorio (`README.md`, `prompts/`, `corridas/`,
`DECISIONES.md`), análisis económico y gobierno/riesgo. Esta consigna
reemplazó al pedido original: el caso de negocio del docx pasó a ser **el
caso real** sobre el que se construye el sistema agéntico pedido por la
materia, no un fin en sí mismo.

## Iteración 2 — Dos bloqueos reales antes de construir: API key y repo

Antes de escribir código se identificaron dos decisiones que no se podían
inventar:

1. **API key de Anthropic**: el requisito 2 pide corridas reales con costos
   de tokens reales, lo que implica llamar de verdad a la API. No había una
   `ANTHROPIC_API_KEY` propia disponible. Se le preguntó al usuario; eligió
   la opción "usá esta sesión como el agente" en vez de simular datos o
   esperar a conseguir una key. Esto definió la arquitectura de evidencia:
   ver Iteración 4.
2. **Dónde vive el repo**: el usuario había dicho antes que este trabajo no
   iba en `vanguard-agent` ni `Deuda-App` (los dos repos ya configurados en
   el entorno) — se confirmó explícitamente que había que crear un
   repositorio público nuevo.

## Iteración 3 — Sin API key propia: qué se achicó y por qué

El plan "de libro" era: escribir `agente/legajo_agent.py` (orquestador con
el SDK de Anthropic, herramienta `evaluar_legajo`, salida estructurada) y
correrlo 3 veces contra la API real con una key, capturando
`response.usage` para el costo real por corrida.

Sin key, esa ejecución real de la API no era posible. La alternativa
descartada fue **simular** los outputs (inventar qué "habría dicho" el
modelo) — se descartó explícitamente porque iba en contra del espíritu del
requisito 2 ("corre de verdad... guardadas tal como salieron") y de la
filosofía del curso citada en la consigna ("un sistema honesto con una falla
bien contada vale más que uno pulido que no se entiende").

Lo que se hizo en cambio: **el mismo contrato** (mismo `system_prompt.md`,
mismo `user_prompt.md`, misma herramienta `evaluar_legajo`) se ejecutó de
verdad, pero con Claude actuando dentro de la sesión de Claude Code que
construyó este repo, usando su conector real de Google Drive para leer los
3 legajos de la carpeta compartida, y ejecutando literalmente
`python agente/tools.py` para los dos controles financieros (no estimado a
mano). `agente/legajo_agent.py` queda completo, correteable con una key
propia, como el camino de producción — no es un mock, es código real sin
ejecutar por falta de credencial, documentado como tal en
`corridas/README.md`.

Consecuencia directa en el análisis económico (`ANALISIS_ECONOMICO.md`): al
no tener `response.usage` real de estas 3 corridas, el costo se estimó por
tamaño de caracteres de los prompts reales (conversión ~4 caracteres/token),
método declarado explícitamente en vez de presentarlo como medición exacta.

## Iteración 4 — Por qué el legajo Lopez (rechazado) es la corrida más importante de las 3

Al leer los 3 legajos reales de la carpeta de Drive, dos (Perez, Gonzalez)
aprueban los dos controles y uno (Lopez) los reprueba a ambos. Se evaluó
brevemente si convenía elegir otro tercer legajo "más prolijo" para tener
evidencia más simple, pero se descartó: un sistema que solo se probó contra
casos que aprueban no demuestra que el segundo control (rechazo) funciona.
Lopez quedó como la corrida 3 tal cual salió, incluyendo el detalle de que
sus ingresos son extremadamente volátiles (de ARS 70.000 a ARS 6.000.000 en
6 meses) — un caso realista y no forzado de por qué existe el control de
cuota/ingreso.

## Iteración 5 — Un dato de la fuente estaba mal etiquetado (y había que darse cuenta)

Los 3 archivos "Resumen Carpeta" tienen una fila etiquetada "Reserva
Propiedad" que, en los tres casos, coincide exactamente con el promedio de
los ingresos mensuales informados más abajo en la misma hoja (verificado
recalculando el promedio a mano para los 3 legajos y comparando cifra por
cifra). Es casi seguro un artefacto de celdas combinadas del Excel original
que, al extraerse como texto plano, deja el valor pegado a la etiqueta
equivocada. Se documenta esto en `system_prompt.md` (sección 3) como una
instrucción explícita para el agente — no asumir la etiqueta literal del
campo sin contrastarla con el resto de los datos — en vez de corregirlo
silenciosamente y no dejar rastro.

## Iteración 6 — "Las seis piezas" del contrato y el vocabulario L0–L4: no había definición de cátedra disponible

La consigna menciona ambos conceptos como si ya se hubieran dado en clase,
pero no se tuvo acceso a esa definición exacta al construir este sistema.
En vez de omitir la sección o inventar sin decirlo, se adoptó explícitamente
un framework estándar para cada uno (ver la nota al principio de
`prompts/system_prompt.md` y la sección 0 de `GOBIERNO_Y_RIESGO.md`) y se
dejó constancia acá. Si la cátedra dio una definición distinta, el ajuste es
mecánico: renombrar las secciones existentes, no rediseñar el sistema.

## Iteración 7 — Elección de modelo

Se evaluaron `claude-haiku-4-5`, `claude-sonnet-5` y `claude-opus-5` para
`agente/legajo_agent.py`. Se eligió Haiku 4.5 porque la tarea (extracción
acotada + una tool call + JSON de esquema fijo, con la aritmética ya sacada
del LLM) no necesita el razonamiento de un modelo más grande — ver
`ANALISIS_ECONOMICO.md` para la comparación de costo entre los tres.

## Iteración 8 — Se consiguió una API key real y se corrió el agente de verdad

El usuario pidió cómo conseguir una `ANTHROPIC_API_KEY` propia y la pasó por
el chat para que este agente la usara. Dos problemas prácticos, en orden:

1. La primera key que pasó no estaba asociada a un workspace
   (`This API key is not scoped to a workspace...`, error 400) — Anthropic
   la rechazó pidiendo un header `anthropic-workspace-id` o una key generada
   *dentro* de un workspace específico. Se le explicó la diferencia y generó
   una segunda key desde la pestaña "API Keys" de un workspace concreto, que
   sí funcionó.
2. Con la key correcta, se corrió `agente/correr_corridas_reales.py` (un
   driver nuevo que lee `corridas/*/entrada.md` — el mismo texto real
   capturado de Drive en la Iteración 3 — y llama a
   `legajo_agent.correr_agente()` de verdad, dos llamadas por legajo: una
   con `tool_choice` forzado a `evaluar_legajo`, otra con
   `output_config.format` para el JSON final). Esta corrida sí generó
   `response.usage` real: costo total de las 3 corridas, USD 0,0305; ver
   Iteración 9 para por qué se volvió a correr una segunda vez.

`corridas/*/metadata.json` y `ANALISIS_ECONOMICO.md` se actualizaron con el
costo medido real, reemplazando la estimación por caracteres de la
Iteración 3.

## Iteración 9 — La primera corrida real encontró un bug de verdad (y se corrigió)

Al revisar el resultado real de la primera corrida contra la API (Iteración
8), el legajo **Lopez** — el único de los tres que debía rechazarse — salió
con el Control 1 en **"ok credito" (36,1%)**, contradiciendo el 43,2% que
arroja el propio Excel del legajo y el cálculo determinista de
`agente/tools.py`. Comparando la entrada real:

- La versión de `evaluar_legajo` de ese momento recibía
  `ingreso_neto_mensual_ars` como un único número **ya promediado por el
  LLM**. Para Lopez, el modelo calculó un promedio de ARS 2.038.609 sobre
  los 6 meses informados (ARS 70.000 a ARS 6.000.000) — el promedio correcto
  es ARS 1.702.509,50. Un error de aritmética del modelo, exactamente el
  tipo de falla que el diseño decía evitar ("el LLM nunca hace la cuenta"),
  colado por una rendija: la cuenta que sí hacía el LLM era el promedio de
  ingresos, no el control final.
- Además, tanto Perez (Control 2: 21,6% en vez de 20,4%) como Lopez (Control
  2: 42,9% en vez de 40,5%) mostraron el LTV calculado con "Total Crédito
  (Fee incluido)" en vez de "Crédito Aprobado" — dos cifras distintas en el
  resumen que el modelo no distinguió de forma consistente. En Perez no
  cambiaba el resultado final (ambos valores aprueban); en Lopez tampoco
  cambiaba el resultado final (ambos valores rechazan), pero si el negocio
  tuviera el límite más cerca del 40-42%, sí habría cambiado una aprobación.

**Corrección aplicada** (no fue un ajuste de prompt nada más — fue un
cambio de contrato de la herramienta): `evaluar_legajo` ahora recibe
`ingresos_mensuales_ars` como **lista cruda**, y el promedio (más un cálculo
de volatilidad) lo hace `agente/tools.py::promediar_ingresos`, código
determinista. Se agregó también una regla explícita de negocio: usar
siempre "Crédito Aprobado" (nunca "Total Crédito con fee") para el Control 2.
Ambos cambios se reflejan en `prompts/system_prompt.md`,
`prompts/user_prompt.md` y el `input_schema` de la tool en
`agente/legajo_agent.py`.

Se volvió a correr `agente/correr_corridas_reales.py` con la key real. Los
tres resultados finales coincidieron esta vez, número a número, con
`agente/tools.py` corrido en modo standalone:

| Legajo | Control 1 | Control 2 | Resultado |
|---|---|---|---|
| Perez | 27,3% | 20,4% | ok crédito aprobado |
| Gonzalez | 39,4% | 27,5% | ok crédito aprobado |
| Lopez | 43,2% | 40,5% | crédito no aprobado |

Esto es, de las 9 decisiones documentadas en este proyecto, la más
importante para la nota del requisito 4: no es una falla hipotética
mencionada por cumplir — es una falla real, encontrada corriendo el sistema
de verdad contra la API, con impacto real (cambiaba si a alguien se le
aprobaba o no un crédito), y cerrada con un cambio de diseño verificable
(no con una instrucción de prompt más estricta, que no habría garantizado
nada). Ver `GOBIERNO_Y_RIESGO.md` §2 para el registro de este riesgo ya
cerrado.

## Iteración 10 — El usuario encontró un segundo problema real: un mes de ingreso no coincide con los comprobantes

Después de entregado el proyecto, el usuario miró el Excel del legajo Lopez
y notó algo que ni el agente ni la revisión anterior habían chequeado: el
ingreso de **agosto** no coincide con "los otros recibos". Hasta ese
momento, tanto `tools.py` como las corridas reales habían tomado los 6
valores mensuales directamente del "Resumen Carpeta" — nunca se habían
cruzado contra los comprobantes reales de la subcarpeta "Ingresos" de cada
legajo (que sí están en la carpeta de Drive, y que la consigna de negocio
original menciona explícitamente como la fuente de acreditación: "Monotri-
butistas: comprobantes de facturación de los últimos 6 meses").

Se abrió la carpeta "Ingresos" de Lopez (6 archivos `0X-2026 Ventas.xlsx`,
uno por mes) y se comparó contra el Resumen Carpeta:

| Mes | Resumen Carpeta | Comprobante real | ¿Coincide? |
|---|---|---|---|
| Marzo–Junio | (4 valores) | idénticos | Sí |
| **Julio** | ARS 1.741.680 (= junio, calcado) | **ARS 1.654.750** | No |
| **Agosto** | ARS 6.000.000 | **ARS 6.500.000** | No |

El usuario tenía razón en dos niveles distintos, no en uno solo:

1. **Los números del resumen no coinciden con la documentación real** —
   julio parece un copy-paste de junio, agosto está redondeado.
2. **Más allá de cuál número se use, agosto es un valor atípico** frente al
   resto: la mediana de los otros 5 meses es ARS 379.192 (con comprobantes
   reales) y agosto es >6x esa mediana — una sola factura, al mismo cliente
   único de todo el legajo, muy por encima de cualquier patrón normal de
   facturación. Promediarlo sin más, como si fuera un mes de actividad
   normal, es tratar como "ingreso recurrente" algo que necesita
   verificación documental adicional antes de contar para un crédito
   hipotecario a 5 años.

**Se verificaron también Perez y Gonzalez** contra sus propias carpetas
"Ingresos" para confirmar que el problema era específico de Lopez y no un
patrón general: Gonzalez coincide exacto en los 6 meses (sumando varias
facturas por mes a distintos clientes); Perez tiene diferencias de <1,5%
entre el resumen y el recibo de sueldo real (redondeo normal, no un error).
Ninguno de los dos tiene meses atípicos. El problema es real y es
específico del legajo que ya se iba a rechazar.

**Corrección aplicada**:

1. `agente/tools.py::promediar_ingresos` ahora calcula también la mediana y
   detecta meses "atípicos" (> 3× la mediana del resto), devolviéndolos en
   `outliers`. `evaluar_legajo` los reporta en un campo nuevo,
   `advertencias`, independiente de si los controles 1 y 2 aprueban o no —
   para que un ingreso atípico no quede escondido dentro de un resultado
   "aprobado".
2. `prompts/system_prompt.md` y `user_prompt.md` ahora instruyen
   explícitamente: cuando el legajo trae comprobantes reales además del
   resumen, los comprobantes son la fuente de verdad, y cualquier
   `advertencias` de la herramienta se copia tal cual a `observaciones` —
   nunca se resume ni se omite.
3. `corridas/corrida_03_lopez/entrada.md` se actualizó con los 6
   comprobantes reales y una tabla explícita de discrepancias, para que la
   corrida sea reproducible con la fuente correcta (no con el resumen que
   tenía el error). `corrida_01_perez` y `corrida_02_gonzalez` se
   actualizaron con su propia verificación cruzada (ambos, sin hallazgos).
4. Se volvió a correr `agente/correr_corridas_reales.py` contra la API real.
   El resultado de Lopez sigue siendo rechazo (ahora con Control 1 en 41,5%
   en vez de 43,2%, porque el ingreso real de julio es más bajo que el que
   tenía el resumen — el resultado final no cambia, pero el número sí es
   más correcto), y la salida real del modelo copió la advertencia del mes
   atípico en `observaciones` sin que se lo pidiera dos veces.

**Por qué importa para la nota**: el requisito 6 (gobierno y riesgo) pide
"qué revisás vos antes de confiar en una salida" — este es un ejemplo real
de eso funcionando en la dirección correcta: un humano (el usuario, revisando
el Excel entregado) encontró algo que el agente no había chequeado, y el
sistema se corrigió para que la próxima vez lo detecte solo. Es la segunda
vez en este proyecto (después de la Iteración 9) que una revisión externa
—no un ajuste preventivo de prompt— es lo que realmente mejora el sistema.
Ver `GOBIERNO_Y_RIESGO.md` §2 y §4 para cómo queda reflejado este hallazgo.
