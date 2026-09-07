# Corrida 2 — Legajo Gonzalez (Crédito #2)

- **Fecha/hora**: 2026-09-07 (extracción vía Google Drive)
- **Herramienta usada**: `mcp__Google_Drive__search_files` con
  `query: "parentId = '153SvV_5_G5WMEj5l2XpqtIOPOzCGCr1E'"` (carpeta
  "Crédito 2 - Gonzalez")
- **Archivo fuente**: `02 - #2 Gonzalez.xlsx`
  (fileId `14quzfZ8_EIaIHt4cGXWTDC0Gse86S0Ea`)

## Resumen Carpeta (texto crudo devuelto por Drive, hoja "Resumen Carpeta")

```
Resumen Carpeta ,Préstamo:,#2,,,,,,,,,,,,
,,,,,,,,,,,,,,Plazo Años:
,Propiedad a nombre de:,Gonzalez,,,Oficina RE/MAX:,,,Nombre:,Gonzalez,,,,1
,Hijos:,2,,,Ubicación:,,,Empresa:,MONOTRIBUTISTA,,,,2
,Unica y permanente:,SI,,,Agente:,,,Cargo:,PROFESOR DE INGLES,,,,3
,Primera Propiedad:,SI,,,Oferta Propiedad: ,,,Antigüedad:,9 AÑOS,,,,4
,Ubicación:,MAR DEL PLATA,,,Reserva Propiedad: ,,,,"ARS 2,709,944",,,,5
,Comentarios: ,"Reservo propiedad en Barrio La Florida para uso familiar casa
 habitación, Mar del Plata. Pablo Gonzlez es profesor de ingles, es
 monotributista cat C. Factura por mes minimo 2 millones. Soltero. Vivienda
 única.",,,,,,Veraz:,934,,,,,
,,,,,,,,Compromiso Mensual: ,"ARS 262,566",,,,,
,,,,,,,,Endeudamiento:,"ARS 1,031,000",,,,,
,Información Crédito:,,,,,,,Máximo Atraso 24m:,0 - 30 días,,,,,
,Valor Mercado Propiedad:,"USD 120,000",,,Plazo Años:,5,,Situacion actual:,1,,,,,
,Crédito Aprobado:,"USD 33,000",,,Cuotas:,60,,,,,,,,
,Fee (Otorg. y Gastos Adm.):,"USD 1,997",,,Cuota Mensual:,USD 805.26,,Ingresos Netos,,,,,,
,Total Crédito (Fee incluido):,"USD 34,997",,,Tipo de Cambio,1325,,Gonzalez,,,,,,
,% Valor Propiedad:,27.5%,,,Cuota Mensual:," $ 1,066,974.90 ",,MARZO,ABRIL,MAYO,JUNIO,JULIO,AGOSTO
,,,,,Relacion Cuota/Ingreso:,39%,,"ARS 2,758,900","ARS 2,150,300","ARS 2,945,600","ARS 3,029,535","ARS 2,635,650","ARS 2,739,680"
,TNA,TEM,TEA,,,,,,,,,,,
,13.50%,1.13%,14.58%,, Verificado ,,,MAYO,JUNIO,JULIO,,,,
,,,,,Clausula,OK,,,,,,,,
,,,,,Valor ,OK,,,,,,,,
```

(Se omite el cuadro de amortización mes a mes de las 60 cuotas — no es
insumo de los dos controles financieros y no cambia el resultado.)

## Verificación contra comprobantes reales (carpeta "Ingresos")

A raíz de la Iteración 10 (ver DECISIONES.md), se sumaron las facturas reales
de la carpeta "Ingresos" de este legajo (varias por mes, a distintos
clientes) y se comparó contra el Resumen Carpeta:

| Mes | Resumen Carpeta | Suma de comprobantes reales | ¿Coincide? |
|---|---|---|---|
| Marzo | ARS 2.758.900 | ARS 2.758.900 (4 facturas) | Sí, exacto |
| Abril | ARS 2.150.300 | ARS 2.150.300 (1 factura) | Sí, exacto |
| Mayo | ARS 2.945.600 | ARS 2.945.600 (1 factura) | Sí, exacto |
| Junio | ARS 3.029.535 | ARS 3.029.535 (2 facturas) | Sí, exacto |
| Julio | ARS 2.635.650 | ARS 2.635.650 (2 facturas) | Sí, exacto |
| Agosto | ARS 2.739.680 | ARS 2.739.680 (2 facturas) | Sí, exacto |

Los 6 meses coinciden exactamente. A diferencia del legajo Lopez, este
legajo **no** presenta discrepancias ni meses atípicos.
