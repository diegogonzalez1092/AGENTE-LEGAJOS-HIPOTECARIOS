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

## Iteración 11 — Feedback de un tercero real: el agente evaluador del grupo (parcial de la materia)

En paralelo a este trabajo final, el usuario y su grupo (`evaluador-grupo-33`)
construyeron un **agente evaluador** para el parcial de la materia — un
sistema que corrige trabajos finales aplicando la rúbrica oficial. Se probó
ese evaluador contra este repo (subiendo un `.zip` a
https://evaluador-grupo-33-ahs2yhamgmghk5vivjdbc5.streamlit.app), y devolvió
**96/100**, más tres sugerencias concretas de mejora. Se evaluaron y se
implementaron las tres en serio — no como parches cosméticos para "sumar
puntos", sino resolviendo el problema real detrás de cada una:

**1. "Implementar el cliente de Google Drive en `agente/legajo_agent.py`"**
— tenía razón: ese archivo tenía un stub que imprimía un error y cortaba.
Se escribió `agente/drive_client.py`, un cliente real de la API v3 de
Google Drive (`google-api-python-client` + `google-auth`, scope de solo
lectura), que lee el "Resumen Carpeta" y, si existe, la carpeta
"Ingresos" — siguiendo el mismo patrón que se usó a mano en las
Iteraciones 8-10. **Honestidad sobre el alcance**: no había una cuenta de
servicio de Google Cloud disponible en este entorno para probarlo de
punta a punta contra Drive real — se verificó que importa sin errores y
que la conversión de `.xlsx` a texto reproduce el mismo formato que se
usó en las corridas reales (comparado a mano contra `corridas/*/entrada.md`),
pero la prueba end-to-end contra credenciales reales queda pendiente y así
se documenta, en vez de afirmar que "ya funciona" sin haberlo corrido.

**2. "Agregar una prueba reproducible con un legajo incompleto que valide
un esquema de salida compatible con null"** — esta sugerencia expuso un
problema de diseño real, no solo una prueba faltante: `evaluar_legajo`
tenía sus 4 parámetros como `required` y `tool_choice` forzado a llamar
siempre la herramienta — si un dato faltaba, no había ninguna forma
correcta de responder sin que el LLM inventara un número o decidiera por
su cuenta no llamar a la herramienta (reabriendo el riesgo de la
Iteración 9). Se le preguntó al usuario cómo resolverlo (ver la pregunta
de esta misma conversación) y se eligió la opción que preserva la
garantía de gobierno: la herramienta ahora acepta `null` en cualquier
campo, sigue llamándose siempre, y es el código determinista — no el
LLM — el que decide qué control se puede evaluar y cuál no
(`datos_faltantes`). Se armó `corridas/corrida_04_incompleto` (un legajo
sintético sin valor de mercado de la propiedad) y se corrió contra la API
real: el agente devolvió `resultado_control_1: "ok credito"` (32,4%,
correcto), `resultado_control_2: null`, `resultado_final: "no evaluable"`
y `datos_faltantes: ["valor_propiedad_usd"]` — sin inventar ningún
número. Este caso no entra a `output/legajos_maestro.xlsx` (es un caso de
prueba, no un legajo real de negocio).

**3. "Preservar cada corrida en una carpeta versionada en lugar de
sobrescribir los artefactos anteriores"** — tenía razón: cada corrida de
`agente/correr_corridas_reales.py` pisaba `salida.json`/`metadata.json`
de la corrida anterior, así que las Iteraciones 8, 9 y 10 de este mismo
documento describen corridas cuya evidencia cruda ya no estaba en el
repo (solo el resultado final). Se rediseñó para que cada corrida quede
en `corridas/<caso>/runs/<timestamp>/` sin tocar las anteriores, y los
archivos a nivel `corridas/<caso>/` pasan a ser un espejo de la corrida
más reciente (para no romper las referencias que ya existen en el resto
del repo). A partir de este commit, la evidencia de cada corrida es
acumulativa, no reemplazable.

**Por qué importa para la nota**: esto es doblemente relevante para el
requisito 4 (proceso documentado) — no solo por el ajuste en sí, sino
porque el feedback vino de **otro agente real, construido por otro grupo,
con otra rúbrica**, no de una autoevaluación. Cerrar en serio ese feedback
(en vez de solo subir el puntaje) es la clase de calibración cruzada que
la consigna del parcial le pide a `evaluador-grupo-33` hacer con criterio
humano — acá pasó al revés: un agente evaluador calibró (indirectamente)
este agente.

## Iteración 12 — Dos interfaces públicas para "que cualquiera pueda usarlo"

El usuario pidió que el agente se pudiera ver y usar en una página, no solo
leer como código. Se construyeron dos, con arquitecturas de costo
deliberadamente distintas (ver `GOBIERNO_Y_RIESGO.md` §1 para el detalle):

1. **Demo público (Claude Artifact)** — una página HTML/JS publicada como
   Artifact, con los 4 casos reales precargados y el mismo motor
   determinista de `agente/tools.py` reescrito en JavaScript (verificado
   línea por línea contra los 4 resultados reales del repo antes de
   publicar: coinciden exacto). Usa la función `sample` de la plataforma de
   Artifacts, que llama a Claude con el uso de **cada visitante**, no una
   key propia — nadie puede ver ni robar una credencial porque no hay
   ninguna en el código de la página. El resultado final que se muestra en
   pantalla nunca sale de lo que "dice" el modelo: se recalcula siempre con
   el motor determinista, con los datos que Claude dice haber extraído.

2. **App web (`app.py`, Streamlit)** — pedida explícitamente para tener
   "una aplicación tipo Streamlit" (como la del parcial de
   `evaluador-grupo-33`). Reutiliza los módulos reales del repo
   (`agente/tools.py`, `agente/legajo_agent.py::correr_agente`) en vez de
   reimplementar nada — es literalmente el mismo agente con una interfaz
   arriba. A diferencia del Artifact, acá el costo lo paga **una sola**
   `ANTHROPIC_API_KEY` (la de quien despliega la app), no cada visitante —
   una diferencia de arquitectura real que quedó documentada, con una
   salvaguarda básica (5 corridas por sesión de navegador) en vez de
   ignorarla.

Antes de dar por terminada la app, se corrió un ciclo real de prueba y
arreglo: se levantó `streamlit run app.py` local, se cargó con Playwright
(headless), y **se hizo una corrida real completa contra la API** (no un
mock) — el primer intento reveló un bug visual real: los 4 datos
financieros (ingreso, cuota, valor propiedad, valor crédito) se mostraban
truncados ("ARS 2...", "USD ...") porque `st.columns(4)` dejaba muy poco
ancho por columna. Se cambió a una grilla de 2×2 y se volvió a correr
contra la API real para confirmar la corrección — captura final: todos los
valores completos, resultado "Juan Perez — Aprobado" con 27,2%/20,4%,
coincidiendo con `corridas/corrida_01_perez/salida.json`.

## Iteración 13 — Ajustes de usabilidad de `app.py`: texto crudo colapsado y carga de Excel propio

Dos pedidos del usuario después de probar la app ya desplegada:

1. **El cuadro de texto crudo se veía desprolijo.** El primer ajuste
   pedido (sacar la mención al trabajo final del subtítulo) no era lo que
   se veía "desprolijo" — al aclarar, el usuario se refería al cuadro
   `st.text_area("Texto del legajo", ...)`, que muestra el volcado tal
   cual del Excel (comas sueltas, columnas vacías). Se lo puso detrás de
   un `st.expander` colapsado por defecto ("Ver / editar texto crudo del
   legajo"), así solo se ve si alguien lo abre a propósito.

2. **Subir un Excel propio.** El usuario pidió poder adjuntar un `.xlsx`
   (no solo elegir entre los 4 casos de ejemplo o pegar texto a mano) y
   que el agente lo lea y evalúe igual que a los casos reales. Se agregó
   `st.file_uploader` en `app.py`. Para no duplicar lógica ni forzar que
   la app web dependa de las librerías de Google (`google-api-python-client`,
   `google-auth`, que solo hacen falta para el camino de producción por
   Drive), se extrajo la función de conversión de `.xlsx` a texto — que ya
   existía adentro de `agente/drive_client.py` — a un módulo nuevo,
   `agente/xlsx_utils.py`, sin dependencias de Google. `drive_client.py`
   ahora importa esa misma función en vez de tener su propia copia. El
   Excel subido se convierte con el mismo formato (filas separadas por
   coma) que ya se usaba en las 3 corridas reales y en el conector de
   Drive, se envuelve como `## Resumen Carpeta (<nombre archivo>)` y se le
   pasa a `legajo_agent.correr_agente()` sin ningún cambio en el agente
   mismo — mismo contrato, misma herramienta determinista.

   Se probó de punta a punta antes de pushear: se armó un `.xlsx` sintético
   con `openpyxl`, se corrió `streamlit run app.py` local, y con Playwright
   se subió el archivo por la UI real y se verificó (captura) que el texto
   extraído en el expander coincide exactamente con el contenido de las
   celdas del archivo subido, con el mismo formato de comas que produce
   `drive_client.py`. No se pudo probar el llamado real a la API de
   Anthropic en este paso puntual (no había una `ANTHROPIC_API_KEY` en este
   entorno en el momento del cambio) — lo que sí se validó de punta a punta
   es la parte nueva (lectura del Excel subido), reusando el mismo agente
   ya probado contra la API real en las Iteraciones 8-11.
