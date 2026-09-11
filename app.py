"""
El Sello del Legajo — interfaz web (Streamlit) del agente de análisis
financiero de legajos hipotecarios.

Es el mismo agente que `agente/legajo_agent.py`: Claude extrae los datos del
texto crudo del legajo y llama a `evaluar_legajo` (código determinista de
`agente/tools.py`) para los dos controles financieros — el modelo nunca
calcula los porcentajes, la app tampoco le muestra al usuario un número que
no haya salido de esa función. Ver DECISIONES.md, GOBIERNO_Y_RIESGO.md.

A diferencia del demo publicado como Artifact (que corre con el uso de
Claude de cada visitante, sin ninguna key expuesta), esta app usa UNA sola
ANTHROPIC_API_KEY configurada como secreto — todo el que la use consume la
misma cuenta. Por eso hay un límite de corridas por sesión de navegador
(ver LIMITE_CORRIDAS_POR_SESION más abajo) — no es un rate-limit robusto,
es una salvaguarda razonable para una demo de clase, documentada como tal
en el README.

Cómo correrla localmente:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...
    streamlit run app.py

Cómo desplegarla (Streamlit Community Cloud, gratis): ver README.md.
"""

from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "agente"))

LIMITE_CORRIDAS_POR_SESION = 5

# La API key sale de st.secrets en Streamlit Cloud, o de la variable de
# entorno si se corre local — legajo_agent.py / anthropic.Anthropic() leen
# ANTHROPIC_API_KEY del entorno, así que la copiamos ahí si vino de secrets.
try:
    if "ANTHROPIC_API_KEY" in st.secrets and not os.environ.get("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    pass  # sin secrets.toml en local — se espera la variable de entorno

st.set_page_config(page_title="El Sello del Legajo", page_icon="🏛️", layout="wide")

# ---------------------------------------------------------------------
# Los 4 casos reales de corridas/ — mismo texto que recibe el agente real
# (todo desde el primer encabezado "## " en adelante, igual que
# agente/correr_corridas_reales.py::parsear_entrada).
# ---------------------------------------------------------------------
PRESETS = {
    "Perez — aprobado": {
        "dot": "🟢",
        "resumen": "Control 1: 27% · Control 2: 20%",
        "texto": '''## Resumen Carpeta (texto crudo devuelto por Drive, hoja "Resumen Carpeta")

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

## Verificación contra comprobantes reales (carpeta "Ingresos")

Los 3 recibos de sueldo reales de este legajo (junio ARS 2.580.000, julio
ARS 2.823.000, agosto ARS 2.763.000) difieren del resumen en menos de 1,5%
(redondeo normal) — no hay discrepancias ni meses atípicos.''',
    },
    "Gonzalez — aprobado (margen ajustado)": {
        "dot": "🟢",
        "resumen": "Control 1: 39% (ajustado) · Control 2: 27%",
        "texto": '''## Resumen Carpeta (texto crudo devuelto por Drive, hoja "Resumen Carpeta")

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

## Verificación contra comprobantes reales (carpeta "Ingresos")

Las facturas reales de los 6 meses (varias por mes, a distintos clientes)
coinciden EXACTO con el resumen — sin discrepancias ni meses atípicos.''',
    },
    "Lopez — rechazado": {
        "dot": "🔴",
        "resumen": "Control 1: 41% · Control 2: 41% — rechazado",
        "texto": '''## Hallazgo: el resumen no coincide con los comprobantes reales

Comparando el "Resumen Carpeta" contra los 6 comprobantes reales de
facturación de la carpeta "Ingresos":

| Mes | Resumen Carpeta | Comprobante real | ¿Coincide? |
|---|---|---|---|
| Marzo | ARS 282.505 | ARS 282.505 | Sí |
| Abril | ARS 70.000 | ARS 70.000 | Sí |
| Mayo | ARS 379.192 | ARS 379.192 | Sí |
| Junio | ARS 1.741.680 | ARS 1.741.680 | Sí |
| Julio | ARS 1.741.680 (idéntico a junio) | ARS 1.654.750 | NO |
| Agosto | ARS 6.000.000 | ARS 6.500.000 | NO |

El valor de julio del resumen es igual al de junio (parece un copy-paste al
cargar el dato). Además, agosto es un valor atípico extremo: la mediana de
los otros 5 meses (con los comprobantes reales) es ARS 379.192, y agosto es
~17x esa mediana — una sola factura, al mismo cliente único de todos los
meses. Usá los comprobantes reales, no el resumen, para los ingresos.

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

## Comprobantes reales de facturación (carpeta "Ingresos", monotributista)

Un Factura C por mes, siempre al mismo cliente (CUIT 22222222222, "Prueba 1 S.A."):

```
03-2026 Ventas.xlsx — Imp. Total: $ 282,505.00
04-2026 Ventas.xlsx — Imp. Total: $ 70,000.00
05-2026 Ventas.xlsx — Imp. Total: $ 379,192.00
06-2026 Ventas.xlsx — Imp. Total: $ 1,741,680.00
07-2026 Ventas.xlsx — Imp. Total: $ 1,654,750.00
08-2026 Ventas.xlsx — Imp. Total: $ 6,500,000.00
```

Estos son los valores a usar para ingresos_mensuales_ars — no los del Resumen Carpeta.''',
    },
    "Martinez — legajo incompleto": {
        "dot": "🟡",
        "resumen": "Falta valor de propiedad — no evaluable",
        "texto": '''## Legajo incompleto (caso de prueba)

Este legajo no trae valor de mercado de la propiedad (está "PENDIENTE DE
TASACIÓN") — es un dato obligatorio para el Control 2. No se debe inventar
ese valor: hay que pasar null y evaluar solo lo que se pueda.

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
TASACIÓN" en vez de un número — el agente no debe interpretar eso como `0`
ni inventar un valor de mercado; debe pasar `null` en `valor_propiedad_usd`.''',
    },
}


# ---------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------
st.title("🏛️ El Sello del Legajo")
st.caption(
    "Agente de análisis financiero de legajos hipotecarios — Trabajo final, "
    "Programación de y con Agentes de IA, MBA UCEMA. "
    "[Ver el repo completo](https://github.com/diegogonzalez1092/agente-legajos-hipotecarios)."
)

if "corridas_usadas" not in st.session_state:
    st.session_state.corridas_usadas = 0

col_izq, col_der = st.columns([1, 1], gap="large")

with col_izq:
    st.subheader("1 · Elegí un legajo")
    st.caption("Los 4 casos reales de `corridas/`, con su texto real — o editalo / pegá el tuyo.")

    caso = st.radio(
        "Caso",
        list(PRESETS.keys()),
        format_func=lambda k: f"{PRESETS[k]['dot']} {k} — {PRESETS[k]['resumen']}",
        label_visibility="collapsed",
    )
    texto_legajo = st.text_area("Texto del legajo", value=PRESETS[caso]["texto"], height=380)

    restantes = LIMITE_CORRIDAS_POR_SESION - st.session_state.corridas_usadas
    analizar = st.button(
        f"Analizar legajo ({restantes} corrida{'s' if restantes != 1 else ''} restante{'s' if restantes != 1 else ''} en esta sesión)",
        type="primary",
        disabled=restantes <= 0,
    )
    if restantes <= 0:
        st.caption(
            "Llegaste al límite de corridas de esta demo pública (protege el presupuesto de la API). "
            "Recargá la página para reiniciar el contador, o corré el repo con tu propia API key."
        )

with col_der:
    st.subheader("2 · Resultado")
    st.caption("Extracción por IA + cálculo determinista, igual que en producción.")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error(
            "Falta configurar `ANTHROPIC_API_KEY`. Si estás desplegando esta app, "
            "agregala en **App settings → Secrets** (Streamlit Community Cloud) — ver README.md."
        )
    elif analizar:
        st.session_state.corridas_usadas += 1
        with st.spinner("Analizando el legajo…"):
            try:
                import legajo_agent  # import diferido: recién acá hace falta la API key

                resultado = legajo_agent.correr_agente(caso, "app.py (Streamlit)", texto_legajo)
                salida = resultado["salida"]
                uso = resultado["uso_tokens"]

                r = salida.get("resultado_final")
                if r == "ok credito aprobado":
                    st.success(f"### ✅ {salida.get('cliente') or 'Cliente'} — Aprobado")
                elif r == "credito no aprobado":
                    st.error(f"### ⛔ {salida.get('cliente') or 'Cliente'} — No aprobado")
                else:
                    st.warning(f"### ⚠️ {salida.get('cliente') or 'Cliente'} — No evaluable")

                st.caption(
                    f"{salida.get('jurisdiccion') or 'Jurisdicción no informada'} · "
                    f"Crédito {salida.get('nro_credito') or 's/n'}"
                )

                c1, c2 = st.columns(2)
                with c1:
                    pct1 = salida.get("control_1_pct")
                    st.metric("Control 1 — Cuota/Ingreso", f"{pct1}%" if pct1 is not None else "sin datos")
                    if pct1 is not None:
                        st.progress(min(1.0, pct1 / 100))
                    st.caption(f"Límite: 40% · {salida.get('resultado_control_1')}")
                with c2:
                    pct2 = salida.get("control_2_pct")
                    st.metric("Control 2 — LTV", f"{pct2}%" if pct2 is not None else "sin datos")
                    if pct2 is not None:
                        st.progress(min(1.0, pct2 / 100))
                    st.caption(f"Límite: 35% · {salida.get('resultado_control_2')}")

                d1, d2 = st.columns(2)
                d1.metric("Ingreso total", f"ARS {salida['total_ingresos_ars']:,.0f}" if salida.get("total_ingresos_ars") is not None else "—")
                d2.metric("Cuota", f"USD {salida['cuota_usd']:,.2f}" if salida.get("cuota_usd") is not None else "—")
                d3, d4 = st.columns(2)
                d3.metric("Valor propiedad", f"USD {salida['valor_propiedad_usd']:,.0f}" if salida.get("valor_propiedad_usd") is not None else "sin dato")
                d4.metric("Valor crédito", f"USD {salida['valor_credito_usd']:,.0f}" if salida.get("valor_credito_usd") is not None else "sin dato")

                if salida.get("motivo"):
                    st.error(f"**Motivo:** {salida['motivo']}")
                if salida.get("datos_faltantes"):
                    st.warning(f"**Datos faltantes:** {', '.join(salida['datos_faltantes'])} — no se inventó ningún valor.")
                if salida.get("observaciones"):
                    st.info(f"**Observaciones de Claude:** {salida['observaciones']}")

                st.divider()
                st.caption(
                    f"Modelo: `{resultado['modelo']}` · "
                    f"Tokens: {uso['input_tokens']} in / {uso['output_tokens']} out · "
                    "Los dos controles fueron calculados por `agente/tools.py` (código determinista), "
                    "no por el modelo — ver GOBIERNO_Y_RIESGO.md."
                )
            except Exception as exc:  # noqa: BLE001 — mostrar cualquier falla de la API al usuario
                st.error(f"No se pudo analizar el legajo: {exc}")
    else:
        st.info("Elegí un legajo a la izquierda y apretá **Analizar legajo**.")
