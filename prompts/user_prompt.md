# User Prompt — Template por legajo

Este es el mensaje de usuario que se le manda al agente por cada legajo. Los
`{{ }}` se reemplazan antes de llamar a la API (ver `agente/legajo_agent.py`,
función `construir_user_prompt`).

```
Analizá el siguiente legajo de crédito hipotecario y devolvé el JSON
estructurado según el formato de salida definido en tu system prompt.

## Legajo: {{ nombre_carpeta }}
## Fuente: {{ ruta_o_id_drive }}
## Fecha de la corrida: {{ fecha_iso }}

### Legajo (texto extraído de Drive: Resumen Carpeta y, si existen, los
comprobantes reales de la carpeta "Ingresos")

{{ resumen_carpeta_texto_crudo }}

### Instrucciones específicas de esta corrida

1. Extraé del texto de arriba: número de crédito, jurisdicción (ubicación de
   la propiedad), nombre del cliente, ingresos mensuales (propios y otros si
   los hay), cuota mensual (en USD, en ARS y el tipo de cambio usado), valor
   de mercado de la propiedad y valor del crédito.
2. Si el texto incluye comprobantes reales (facturación/recibos de sueldo)
   además del "Resumen Carpeta", los comprobantes son la fuente de verdad —
   el resumen puede tener errores de carga. Si un mes no coincide entre el
   resumen y el comprobante, usá el valor del comprobante y decilo en
   `observaciones`.
3. Pasá TODOS los meses de ingreso como lista a `evaluar_legajo` — no los
   promedies vos mismo. La herramienta calcula el promedio, la volatilidad,
   y si algún mes es un valor atípico (`advertencias`). Si `advertencias`
   viene con contenido, copialo tal cual a `observaciones` — no lo resumas
   ni lo omitas.
4. Llamá a la herramienta `evaluar_legajo` con esos números (usando
   "Crédito Aprobado", no "Total Crédito con fee", para valor_credito_usd).
   Si el legajo no trae alguno de los 4 datos, llamá a la herramienta
   IGUAL pasando `null` en ese campo — nunca inventes el número y nunca
   dejes de llamarla.
5. Completá el JSON de salida con el resultado de la herramienta y tu
   extracción de datos. Copiá `datos_faltantes` de la herramienta tal cual,
   y explicá en `observaciones` qué falta.
```

## Variantes

- **Variante "legajo incompleto"**: probada con un caso real de prueba
  (`corridas/corrida_04_incompleto`, ver DECISIONES.md, Iteración 11) — un
  legajo sin valor de mercado de la propiedad. El agente llama a
  `evaluar_legajo` con `valor_propiedad_usd: null`; la herramienta evalúa
  el Control 1 (que sí tiene datos) y devuelve `control_2_ltv: null`,
  `resultado_final: "no evaluable"` y
  `datos_faltantes: ["valor_propiedad_usd"]`. No se agregó ninguna
  instrucción especial al prompt para este caso — la regla 4 de arriba ya
  cubre "pasá `null` si falta un dato", y es la misma para los 3 legajos
  completos y para este caso incompleto.
- **Variante "comprobante contradice el resumen"**: usada de hecho en la
  corrida de Lopez (ver DECISIONES.md, Iteración 10) — el texto de entrada
  incluye tanto el "Resumen Carpeta" como los comprobantes reales de
  facturación de la carpeta "Ingresos", con una nota explícita marcando en
  qué meses no coinciden, para que el agente no tenga que adivinar cuál
  priorizar.
