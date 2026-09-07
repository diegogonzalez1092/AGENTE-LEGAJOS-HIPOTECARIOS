# Agente de Análisis Financiero de Legajos Hipotecarios

Trabajo final — *Programación de y con Agentes de IA*, MBA UCEMA, 2026 2T.

> Nota de formato: la consigna pide "el README estándar de la materia" sin
> adjuntar la plantilla. No tuvimos acceso a ese estándar exacto, así que
> este README sigue una estructura genérica pero completa (qué es, cómo
> corre, qué prueba, dónde está cada requisito de la rúbrica) — ver
> `DECISIONES.md`, Iteración 6.

## Qué es

Un agente que automatiza el paso 3 del circuito de originación de crédito
hipotecario de una empresa real (caso descripto en detalle abajo): el
**análisis financiero** de cada legajo, una vez que Legales ya aprobó el
perfil crediticio del cliente. El agente lee el resumen de cada legajo,
aplica los dos controles financieros duros de la empresa, decide una
recomendación de aprobado/rechazado con motivo, y la vuelca a un Excel
maestro.

No es un chatbot: tiene un contrato escrito (`prompts/`), una herramienta
determinista para el cálculo financiero y un conector real de archivos
(Google Drive) para la lectura de legajos, salida estructurada (JSON con
esquema fijo), y puntos de supervisión humana explícitos con vocabulario
L0–L4 (ver `GOBIERNO_Y_RIESGO.md`) — el agente nunca aprueba un crédito por
sí mismo, solo prepara la recomendación que un Gerente de Riesgo firma.

## El caso real

Empresa que otorga créditos hipotecarios. Circuito completo:

1. El asesor de inversión hace el análisis preliminar y arma el legajo
   digital; el deudor firma la solicitud de servicios.
2. **Legales** estudia el perfil crediticio (BCRA - Central de Deudores,
   Veraz, Nosis, cheques rechazados). *(fuera del alcance de este agente)*
3. **Este agente** hace el análisis financiero:
   - Acreditación de ingresos según condición tributaria (recibo de sueldo /
     facturación de monotributista / DDJJ de Ganancias de autónomo).
   - **Control 1 — Cuota/Ingreso**: la cuota mensual no puede superar el
     **40%** del ingreso neto del cliente.
   - **Control 2 — LTV**: el crédito no puede exceder el **35%** del valor
     de mercado del inmueble en garantía.

Los legajos reales usados para este proyecto viven en una carpeta de Google
Drive compartida por el usuario ("Trabajo Final - Creación agentes de IA"),
con 3 subcarpetas (Perez, Gonzalez, Lopez), cada una con un Excel "Resumen
Carpeta" real.

## Resultado de las corridas reales (contra la API real de Anthropic)

| Legajo | Jurisdicción | Control 1 (cuota/ingreso) | Control 2 (LTV) | Resultado final |
|---|---|---|---|---|
| Perez (#1) | Mar del Plata | 27,2% — OK | 20,4% — OK | **ok crédito aprobado** |
| Gonzalez (#2) | Mar del Plata | 39,4% — OK (margen ajustado) | 27,5% — OK | **ok crédito aprobado** |
| Lopez (364313) | Córdoba | 41,5% — NO CUMPLE | 40,5% — NO CUMPLE | **crédito no aprobado** + advertencia de ingreso atípico |
| Martinez (caso de prueba, no es un legajo real) | Rosario | 32,4% — OK | sin dato — **no evaluable** | **no evaluable** (falta valor de propiedad) |

Costo real medido (`response.usage`, `claude-haiku-4-5`): **USD 0,0472** los
3 legajos de negocio juntos (≈USD 0,0157 por legajo) — ver
`ANALISIS_ECONOMICO.md`.

Esto pasó por tres rondas de corrección real, no una sola:

1. La primera vez que se corrió contra la API real, el resultado de Lopez
   vino mal por un bug de promedio de ingresos calculado por el modelo
   (Iteración 9).
2. Después de entregado, el usuario notó — mirando el Excel — que el ingreso
   de agosto de Lopez no coincidía con los comprobantes reales de la
   carpeta "Ingresos" de Drive. Se verificó, se confirmó (y se vio que ese
   mismo mes es además un valor atípico, 6,4x la mediana del resto), y se
   agregó detección determinista de ingresos atípicos al agente
   (Iteración 10).
3. El agente evaluador del parcial del grupo del usuario
   (`evaluador-grupo-33`) calificó este repo con 96/100 y devolvió 3
   sugerencias concretas — las tres se implementaron en serio: cliente real
   de Google Drive, esquema con `null` para legajos incompletos (probado
   con el legajo sintético "Martinez" de arriba), y corridas versionadas
   sin sobrescribirse (Iteración 11).

Ver `DECISIONES.md` para la historia completa de las tres — es la evidencia
más importante del proyecto: no fallas mencionadas por cumplir, sino fallas
y feedback reales, encontrados corriendo y revisando el sistema de verdad
(dos veces por el propio proceso, una vez por un agente evaluador externo).

Detalle completo, entrada real y JSON de salida de cada corrida:
[`corridas/`](corridas/). Excel maestro con las 3 filas ya cargadas:
[`output/legajos_maestro.xlsx`](output/legajos_maestro.xlsx).

## Estructura del repo

```
README.md                    — este archivo
prompts/
  system_prompt.md           — contrato del agente (rol, objetivo, reglas, herramientas, formato)
  user_prompt.md              — template del mensaje por legajo
agente/
  tools.py                    — controles financieros deterministas (evaluar_legajo)
  drive_client.py               — cliente real de Google Drive API v3 (producción)
  excel_writer.py              — escritura del Excel maestro (conector real #2)
  legajo_agent.py               — orquestador de producción (SDK de Anthropic + tool use)
  generar_excel_maestro.py       — reconstruye output/legajos_maestro.xlsx desde corridas/*/salida.json
  correr_corridas_reales.py      — corre las 4 corridas contra la API real, versionadas
  requirements.txt
corridas/
  README.md                    — cómo se ejecutaron las corridas reales
  corrida_01_perez/            — entrada.md, salida.json, fecha.txt, metadata.json (+ runs/<timestamp>/)
  corrida_02_gonzalez/
  corrida_03_lopez/
  corrida_04_incompleto/        — caso de prueba sintético (legajo sin valor de propiedad)
output/
  legajos_maestro.xlsx          — el Excel maestro pedido por el caso de negocio (solo los 3 legajos reales)
DECISIONES.md                  — historia del proceso: iteraciones, fallas, decisiones
ANALISIS_ECONOMICO.md          — costo por corrida, proyección, elección de modelo
GOBIERNO_Y_RIESGO.md           — permisos, riesgos, supervisión L0–L4, quién firma
```

## Cómo correrlo

### Reconstruir el Excel maestro (no requiere API key)

```bash
pip install openpyxl
python agente/generar_excel_maestro.py
```

Lee las 3 salidas ya guardadas en `corridas/*/salida.json` y regenera
`output/legajos_maestro.xlsx` desde cero — reproducible por cualquiera sin
credenciales.

### Verificar los controles financieros de las 3 corridas reales (no requiere API key)

```bash
python agente/tools.py
```

Corre los dos controles deterministas sobre los 3 legajos reales y muestra
los mismos porcentajes documentados en `corridas/`.

### Reproducir las corridas reales contra la API (requiere API key propia)

```bash
pip install -r agente/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python agente/correr_corridas_reales.py
```

Corre `legajo_agent.correr_agente()` de verdad para los 3 legajos de negocio
más el caso de prueba "legajo incompleto", usando el texto ya capturado en
`corridas/*/entrada.md` (no necesita Drive). Cada corrida se archiva en
`corridas/<caso>/runs/<timestamp>/` sin pisar las anteriores, y actualiza el
espejo de "última corrida" + `output/legajos_maestro.xlsx` (solo con los 3
legajos de negocio). Esto es lo que efectivamente se corrió para esta
entrega — ver `DECISIONES.md`, Iteraciones 8, 9, 10 y 11.

### Correr el agente contra un legajo nuevo, vía Drive (camino de producción)

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/ruta/a/credenciales-cuenta-servicio.json
export ANTHROPIC_API_KEY=sk-ant-...
python agente/legajo_agent.py --drive-folder-id <ID_DE_LA_CARPETA_DEL_LEGAJO>
```

Usa `agente/drive_client.py` (API real de Google Drive) para leer el legajo
directamente de Drive — sin necesidad de un texto ya capturado. **Estado**:
el código sigue la API oficial y se probó que importa y compila sin
errores, pero no se corrió de punta a punta contra una cuenta de servicio
real en este entorno (no había credenciales disponibles) — ver
`DECISIONES.md`, Iteración 11, y `GOBIERNO_Y_RIESGO.md` §2 para el detalle
de qué falta probar antes de usarlo en producción.

## Dónde está cada requisito de la rúbrica

| Requisito | Dónde |
|---|---|
| 1. Sistema completo (contrato, herramienta real, output estructurado, supervisión) | `prompts/`, `agente/tools.py` + conector Google Drive, esquema JSON en `agente/legajo_agent.py`, `GOBIERNO_Y_RIESGO.md` §3 |
| 2. Corre de verdad (3 corridas reales) | `corridas/` |
| 3. Formato estricto | Esta estructura de carpetas |
| 4. Historia del proceso | `DECISIONES.md` |
| 5. Análisis económico | `ANALISIS_ECONOMICO.md` |
| 6. Gobierno y riesgo | `GOBIERNO_Y_RIESGO.md` |
