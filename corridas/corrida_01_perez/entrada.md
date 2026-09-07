# Corrida 1 — Legajo Perez (Crédito #1)

- **Fecha/hora**: 2026-09-07 (extracción vía Google Drive)
- **Herramienta usada**: `mcp__Google_Drive__search_files` con
  `query: "parentId = '1Oj_Fylvver_AfMEKnV1_25PAeJhbOadu'"` (carpeta
  "Crédito 1 - Perez")
- **Archivo fuente**: `01 - #1 Perez.xlsx`
  (fileId `1m4li1wAAHJQ1VuPJs4my600NbqbQaJMh`)

## Resumen Carpeta (texto crudo devuelto por Drive, hoja "Resumen Carpeta")

```
Resumen Carpeta ,Préstamo:,#1,,,,,,,,
,Propiedad a nombre de:,Perez,,,Oficina:,,,Nombre:,Perez,
,Hijos:,0,,,Ubicación:,,,Empresa:,Colegio,
,Unica y permanente:,SI,,,Agente:,,,Cargo:,Representante Legal,
,Primera Propiedad:,SI,,,Oferta Propiedad: ,,,Antigüedad:,2 años y 6 meses,
,Ubicación:,Mar del Plata,,,Reserva Propiedad: ,,,,"ARS 2,707,521",
,Comentarios: ,"Juan Perez es representante legal de un colegio en Mar del
 Plata, tiene un ingreso aprox de $3.000.000. Es soltero. Destino de la
 vivienda de uso familiar. Es primera vivienda.",,,,,,Veraz:,758,
,,,,,,,,Compromiso Mensual: ,-,
,,,,,,,,Endeudamiento:,"ARS 15,558,000",
,Información Crédito:,,,,,,,Máximo Atraso 24m:,0-30,
,Valor Mercado Propiedad:,"USD 98,000",,,Plazo Años:,5,,Situacion actual:,0-30,
,Crédito Aprobado:,"USD 20,000",,,Cuotas:,60,,,,
,Fee (Otorg. y Gastos Adm.):,"USD 1,210",,,Cuota Mensual:,USD 488.04,,Ingresos Netos,,
,Total Crédito (Fee incluido):,"USD 21,210",,,Tipo de Cambio,1515,,Perez,,
,% Valor Propiedad:,20.4%,,,Cuota Mensual:," $ 739,378.83 ",,JUNIO,JULIO,AGOSTO
,,,,,Relacion Cuota/Ingreso:,27%,,"ARS 2,587,123","ARS 2,809,243","ARS 2,726,198"
,TNA,TEM,TEA,,,,,,,
,13.50%,1.13%,14.58%,, Verificado ,,,JUNIO,JULIO,AGOSTO
,,,,,Clausula,ok,,,,
,,,,,Valor de escritura,ok,,,,
```

(Se omite el cuadro de amortización mes a mes de las 60 cuotas — no es
insumo de los dos controles financieros y no cambia el resultado.)

## Verificación contra comprobantes reales (carpeta "Ingresos")

A raíz de la Iteración 10 (ver DECISIONES.md), se cruzaron también los 3
recibos de sueldo reales de la carpeta "Ingresos" de este legajo contra el
Resumen Carpeta:

| Mes | Resumen Carpeta | Recibo de sueldo real (Neto a cobrar) | Diferencia |
|---|---|---|---|
| Junio | ARS 2.587.123 | ARS 2.580.000 | 0,3% |
| Julio | ARS 2.809.243 | ARS 2.823.000 | 0,5% |
| Agosto | ARS 2.726.198 | ARS 2.763.000 | 1,3% |

Diferencias menores (<1,5%), consistentes con redondeo entre el resumen y
el recibo formal — no cambian el resultado de ningún control. A diferencia
del legajo Lopez, este legajo **no** presenta discrepancias significativas
ni meses atípicos.
