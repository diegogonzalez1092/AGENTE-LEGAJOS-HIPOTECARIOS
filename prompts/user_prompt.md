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

### Resumen Carpeta (texto extraído del Excel real del legajo)

{{ resumen_carpeta_texto_crudo }}

### Instrucciones específicas de esta corrida

1. Extraé del texto de arriba: número de crédito, jurisdicción (ubicación de
   la propiedad), nombre del cliente, ingresos mensuales (propios y otros si
   los hay), cuota mensual (en USD, en ARS y el tipo de cambio usado), valor
   de mercado de la propiedad y valor del crédito.
2. Si hay varios meses de ingresos informados, usá el promedio como ingreso
   neto mensual para el Control 1, y mencioná en `observaciones` si hay alta
   volatilidad entre meses.
3. Llamá a la herramienta `evaluar_legajo` con esos números — no calcules
   los porcentajes vos mismo.
4. Completá el JSON de salida con el resultado de la herramienta y tu
   extracción de datos. Si algún dato no está disponible en el resumen,
   usá `null` y explicalo en `observaciones`.
```

## Variantes

- **Variante "legajo incompleto"**: si el `resumen_carpeta_texto_crudo` no
  trae valor de mercado de la propiedad o cuota mensual, se agrega al final
  del prompt: `"Si falta algún dato obligatorio para calcular los controles,
  no llames a evaluar_legajo con valores inventados: devolvé el JSON con
  resultado_final = null y explicá en observaciones qué falta."` No se usó
  en las 3 corridas reales (los 3 legajos venían completos), pero está
  prevista para producción — ver DECISIONES.md.
