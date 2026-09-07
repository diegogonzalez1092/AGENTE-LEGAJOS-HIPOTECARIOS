# Corrida 3 — Legajo Lopez (Crédito 364313)

- **Fecha/hora**: 2026-09-07 (extracción vía Google Drive)
- **Herramienta usada**: `mcp__Google_Drive__search_files` con
  `query: "parentId = '1mosMCswpAzoLuwkWcXbu_qTrMcWhPgCm'"` (carpeta
  "Crédito 3 - Lopez")
- **Archivo fuente (Resumen Carpeta)**: `03 - #3 Lopez.xlsx`
  (fileId `1OVoJ2LE9V6ueCwWATpVpAUGKxbu8iBZ3`)
- **Archivos fuente (comprobantes reales)**: carpeta "Ingresos"
  (fileId `1-mfFjY_wkwDbB1Z6NJq1qFkjsb_1Z231`), 6 archivos
  `0X-2026 Ventas.xlsx` (uno por mes, marzo a agosto 2026)

## Hallazgo (ver DECISIONES.md, Iteración 10)

El usuario notó, mirando el Excel del legajo, que el ingreso de agosto no
coincide con los comprobantes. Se verificó comparando el "Resumen Carpeta"
contra los 6 archivos reales de facturación de la carpeta "Ingresos":

| Mes | Resumen Carpeta | Comprobante real (`0X-2026 Ventas.xlsx`) | ¿Coincide? |
|---|---|---|---|
| Marzo | ARS 282.505 | ARS 282.505 | Sí |
| Abril | ARS 70.000 | ARS 70.000 | Sí |
| Mayo | ARS 379.192 | ARS 379.192 | Sí |
| Junio | ARS 1.741.680 | ARS 1.741.680 | Sí |
| **Julio** | ARS 1.741.680 (idéntico a junio) | **ARS 1.654.750** | **No** |
| **Agosto** | ARS 6.000.000 | **ARS 6.500.000** | **No** |

El valor de julio en el resumen es exactamente igual al de junio — todo
indica que se copió el número de junio por error al cargar julio. El de
agosto está redondeado hacia abajo respecto al comprobante real. Además,
independientemente de cuál de los dos números de agosto se use, **ese mes
es un valor atípico extremo**: la mediana de los otros 5 meses es ARS
379.192, y agosto es entre 15x y 17x esa mediana — una sola factura, al
mismo cliente único de todos los meses ("Prueba 1 S.A.", CUIT 22222222222),
muy por encima de cualquier otro mes del período. Se cruzó también contra
las carpetas "Ingresos" de Perez (coincide, con diferencias <1,5% atribuibles
a redondeo del recibo de sueldo) y Gonzalez (coincide exacto, sumando las
facturas a varios clientes por mes) — el problema es específico de este
legajo, no un error sistemático de extracción.

## Resumen Carpeta (texto crudo devuelto por Drive, hoja "Resumen Carpeta")

```
Resumen Carpeta ,Préstamo:,364313,,,,,,,,,,,,
,,,,,,,,,,,,,,Plazo Años:
,Propiedad a nombre de:,Lopez,,,Oficina,,,Nombre:,Lopez,,,,
,Hijos:,NO,,,Ubicación:,,,Empresa:,MONOTRIBUTO,,,,
,Unica y permanente:,SI,,,Agente:,,,Cargo:,HERRERIA,,,,
,Primera Propiedad:,SI,,,Oferta Propiedad: ,,,Antigüedad:,5 AÑOS,,,,
,Ubicación:,CORDOBA,,,Reserva Propiedad: ,,,,"ARS 1,702,510",,,,
,Comentarios: ,"Propiedad ubicada en Cordoba. Lopez se dedica a la herreria y
 reparacion maquinas viales obras publicas, monotributista.",,,,,,Veraz:,734,,,,,
,,,,,,,,Compromiso Mensual: ,ARS 0,,,,,
,,,,,,,,Endeudamiento:,ARS 0,,,,,
,Información Crédito:,,,,,,,Máximo Atraso 24m:,0-30,,,,,
,Valor Mercado Propiedad:,"USD 53,000",,,Plazo Años:,5,,Situacion actual:,1,,,,,
,Crédito Aprobado:,"USD 21,452",,,Cuotas:,60,,,,,,,,
,Fee (Otorg. y Gastos Adm.):,"USD 1,298",,,Cuota Mensual:,USD 523.47,,Ingresos Netos,,,,,,
,Total Crédito (Fee incluido):,"USD 22,750",,,Tipo de Cambio,1405,,Lopez,,,,,,
,% Valor Propiedad:,40.5%,,,Cuota Mensual:," $ 735,475.99 ",,MARZO,ABRIL,MAYO,JUNIO,JULIO,AGOSTO
,,,,,Relacion Cuota/Ingreso:,43%,,"ARS 282,505","ARS 70,000","ARS 379,192","ARS 1,741,680","ARS 1,741,680","ARS 6,000,000"
,TNA,TEM,TEA,,,,,,,,,,,
,13.50%,1.13%,14.58%,, Verificado ,,,ABRIL,MAYO,JUNIO,JULIO,AGOSTO,SEPTIEMBRE
,,,,,Clausula,,,,,,,,,
,,,,,Valor de escritura,,,,,,,,,
```

(Se omite el cuadro de amortización mes a mes de las 60 cuotas — no es
insumo de los dos controles financieros y no cambia el resultado. Notar que,
a diferencia de Perez y Gonzalez, la fila "Clausula"/"Valor de escritura" de
este legajo viene vacía en la fuente — dato para `observaciones`.)

## Comprobantes reales de facturación (carpeta "Ingresos", monotributista)

Cada archivo es un extracto de "Mis Comprobantes Emitidos" (formato ARCA),
un Factura C por mes, siempre al mismo cliente (CUIT 22222222222, "Prueba 1
S.A."):

```
03-2026 Ventas.xlsx — Factura C, 31/03/2026 — Imp. Total: $ 282,505.00
04-2026 Ventas.xlsx — Factura C, 30/04/2026 — Imp. Total: $ 70,000.00
05-2026 Ventas.xlsx — Factura C, 31/05/2026 — Imp. Total: $ 379,192.00
06-2026 Ventas.xlsx — Factura C, 30/06/2026 — Imp. Total: $ 1,741,680.00
07-2026 Ventas.xlsx — Factura C, 31/07/2026 — Imp. Total: $ 1,654,750.00
08-2026 Ventas.xlsx — Factura C, 31/08/2026 — Imp. Total: $ 6,500,000.00
```

**Estos son los valores que hay que usar para `ingresos_mensuales_ars` — no
los del Resumen Carpeta** (ver tabla de discrepancias más arriba).
