# Corrida 4 — Legajo incompleto (caso de prueba sintético)

- **Fecha/hora**: ver `fecha.txt` / `metadata.json`
- **Origen**: caso de prueba construido a mano, NO es un legajo real de la
  carpeta de Drive del usuario. Se agregó a raíz de la sugerencia del
  agente evaluador del grupo (`evaluador-grupo-33`): "agregar una prueba
  reproducible con un legajo incompleto que valide un esquema de salida
  compatible con null" — ver DECISIONES.md, Iteración 11.
- **Qué prueba**: un legajo al que le falta el valor de mercado de la
  propiedad (dato obligatorio para el Control 2 — LTV). El sistema tiene
  que devolver `resultado_control_2: null`, `resultado_final: "no
  evaluable"` y `datos_faltantes: ["valor_propiedad_usd"]`, **sin inventar
  un valor de propiedad** y sin dejar de llamar a `evaluar_legajo` (la regla
  de gobierno "nunca calcules a mano" se mantiene incluso cuando falta un
  dato — ver `prompts/system_prompt.md`, regla 3).
- **No entra al Excel maestro** (`output/legajos_maestro.xlsx`): es un caso
  de prueba, no un legajo real de negocio — `agente/correr_corridas_reales.py`
  lo corre y guarda la evidencia, pero no lo agrega a esa planilla.

## Resumen Carpeta (texto sintético, con un dato obligatorio faltante a propósito)

```
Resumen Carpeta ,Préstamo:,#4,,,,,,,,
,Propiedad a nombre de:,Martinez,,,Oficina:,,,Nombre:,Martinez,
,Hijos:,1,,,Ubicación:,,,Empresa:,Estudio Contable,
,Unica y permanente:,SI,,,Agente:,,,Cargo:,Contador,
,Primera Propiedad:,SI,,,Oferta Propiedad: ,,,Antigüedad:,4 años,
,Ubicación:,Rosario,,,Reserva Propiedad: ,,,,"ARS 2,016,667",
,Comentarios: ,"Martinez es contador en un estudio contable de Rosario.
 Reservó la propiedad pero todavía no llegó la tasación / informe de valor
 de mercado del inmueble — falta ese dato para completar el legajo.",,,,,,Veraz:,720,
,,,,,,,,Compromiso Mensual: ,-,
,,,,,,,,Endeudamiento:,ARS 0,
,Información Crédito:,,,,,,,Máximo Atraso 24m:,0-30,
,Valor Mercado Propiedad:,PENDIENTE DE TASACIÓN,,,Plazo Años:,5,,Situacion actual:,0-30,
,Crédito Aprobado:,"USD 25,000",,,Cuotas:,60,,,,
,Fee (Otorg. y Gastos Adm.):,"USD 1,500",,,Cuota Mensual:,USD 450.00,,Ingresos Netos,,
,Total Crédito (Fee incluido):,"USD 26,500",,,Tipo de Cambio,1450,,Martinez,,
,% Valor Propiedad:,PENDIENTE,,,Cuota Mensual:," $ 652,500.00 ",,JUNIO,JULIO,AGOSTO
,,,,,Relacion Cuota/Ingreso:,22%,,"ARS 2,000,000","ARS 1,950,000","ARS 2,100,000"
,TNA,TEM,TEA,,,,,,,
,13.50%,1.13%,14.58%,, Verificado ,,,JUNIO,JULIO,AGOSTO
,,,,,Clausula,pendiente,,,,
,,,,,Valor de escritura,pendiente,,,,
```

**Nota**: "Valor Mercado Propiedad" viene explícitamente como "PENDIENTE DE
TASACIÓN" en vez de un número — el agente no debe interpretar eso como
`0` ni inventar un valor de mercado; debe pasar `null` en
`valor_propiedad_usd` a la herramienta `evaluar_legajo`.
