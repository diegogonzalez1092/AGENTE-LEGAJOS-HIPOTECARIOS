"""
Orquestador de producción del Agente de Análisis Financiero de Legajos
Hipotecarios.

Este script es el que correría la empresa en producción, con su propia
ANTHROPIC_API_KEY: lee el resumen de un legajo (Google Drive), lo pasa a
Claude junto con el contrato de prompts/system_prompt.md + user_prompt.md,
deja que el modelo llame a la herramienta determinista evaluar_legajo() para
los dos controles financieros, y escribe el resultado en el Excel maestro.

HISTORIA (ver DECISIONES.md, Iteraciones 3 y 8, y GOBIERNO_Y_RIESGO.md):
la primera versión de este repo no tenía ANTHROPIC_API_KEY propia, así que
las 3 corridas se ejecutaron con Claude actuando dentro de la sesión de
Claude Code que construyó el repo (mismo contrato, mismo cálculo
determinista, distinto canal). Una vez que el usuario consiguió una key
real, se re-corrieron las 3 corridas contra la API de verdad con este mismo
script (ver `agente/correr_corridas_reales.py`), y `corridas/*/salida.json` +
`metadata.json` quedaron con el resultado y el `usage` reales de esa
corrida — no son ambas cosas: son dos generaciones de la misma evidencia,
documentadas por separado para que quede clara la diferencia.

Uso (legajo suelto):
    export ANTHROPIC_API_KEY=sk-ant-...
    python agente/legajo_agent.py --drive-folder-id <ID_DE_LA_CARPETA_DEL_LEGAJO>

Uso (las 3 corridas reales ya guardadas en corridas/, sin Drive):
    export ANTHROPIC_API_KEY=sk-ant-...
    python agente/correr_corridas_reales.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

import anthropic

from tools import evaluar_legajo
from excel_writer import agregar_legajo
from generar_excel_maestro import fila_excel  # una sola definición, ver ese módulo

MODEL = "claude-haiku-4-5"  # ver ANALISIS_ECONOMICO.md por la justificación de elegir el modelo más chico
MAX_TOKENS = 2000

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

with open(os.path.join(REPO_ROOT, "prompts", "system_prompt.md"), encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

EVALUAR_LEGAJO_TOOL = {
    "name": "evaluar_legajo",
    "description": (
        "Aplica los dos controles financieros duros (cuota/ingreso <= 40%, "
        "LTV <= 35%) de forma determinista y devuelve el resultado de cada "
        "uno más la decisión final. Usar SIEMPRE esta herramienta en vez de "
        "calcular los porcentajes en el texto de la respuesta. Pasar la "
        "LISTA cruda de ingresos mensuales tal como aparecen en el legajo — "
        "NUNCA promediarlos vos mismo antes de llamar a la herramienta, el "
        "promedio lo calcula esta función (ver DECISIONES.md, Iteración 9: "
        "un promedio mal calculado por el modelo cambió un resultado en la "
        "primera corrida real). Para valor_credito_usd usá siempre el monto "
        "de 'Crédito Aprobado' del legajo, NUNCA el 'Total Crédito (Fee "
        "incluido)' — son dos montos distintos en el resumen. La herramienta "
        "también devuelve `advertencias` si algún mes de ingreso es un valor "
        "atípico (más de 3x la mediana del resto) — ese mes no debe tratarse "
        "como ingreso recurrente sin verificación adicional, apruebe o no "
        "apruebe el resto de los controles. Si el legajo NO trae alguno de "
        "estos 4 datos, llamá a la herramienta IGUAL — nunca la saltees ni "
        "inventes el número — pasando `null` en el campo que falte. La "
        "herramienta evalúa el control que sí pueda calcular y devuelve "
        "`resultado_final: \"no evaluable\"` con `datos_faltantes` indicando "
        "qué faltó (ver DECISIONES.md, Iteración 11)."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "cuota_mensual_ars": {"type": ["number", "null"]},
            "ingresos_mensuales_ars": {
                "type": ["array", "null"],
                "items": {"type": "number"},
            },
            "valor_credito_usd": {"type": ["number", "null"]},
            "valor_propiedad_usd": {"type": ["number", "null"]},
        },
        "required": [
            "cuota_mensual_ars",
            "ingresos_mensuales_ars",
            "valor_credito_usd",
            "valor_propiedad_usd",
        ],
        "additionalProperties": False,
    },
}

OUTPUT_SCHEMA = {
    "type": "json_schema",
    "schema": {
        "type": "object",
        "properties": {
            "nro_credito": {"type": ["string", "null"]},
            "jurisdiccion": {"type": ["string", "null"]},
            "cliente": {"type": ["string", "null"]},
            "ingresos_propios_ars": {"type": ["number", "null"]},
            "otros_ingresos_ars": {"type": ["number", "null"]},
            "total_ingresos_ars": {"type": ["number", "null"]},
            "cuota_usd": {"type": ["number", "null"]},
            "tipo_cambio": {"type": ["number", "null"]},
            "cuota_ars": {"type": ["number", "null"]},
            "control_1_pct": {"type": ["number", "null"]},
            "resultado_control_1": {
                "type": "string",
                "enum": ["ok credito", "no cumple", "no evaluable"],
            },
            "valor_propiedad_usd": {"type": ["number", "null"]},
            "valor_credito_usd": {"type": ["number", "null"]},
            "control_2_pct": {"type": ["number", "null"]},
            "resultado_control_2": {
                "type": "string",
                "enum": ["ok credito", "no cumple", "no evaluable"],
            },
            "resultado_final": {
                "type": "string",
                "enum": ["ok credito aprobado", "credito no aprobado", "no evaluable"],
            },
            "motivo": {"type": ["string", "null"]},
            "datos_faltantes": {"type": "array", "items": {"type": "string"}},
            "observaciones": {"type": ["string", "null"]},
        },
        "required": [
            "nro_credito", "jurisdiccion", "cliente", "ingresos_propios_ars",
            "otros_ingresos_ars", "total_ingresos_ars", "cuota_usd", "tipo_cambio",
            "cuota_ars", "control_1_pct", "resultado_control_1",
            "valor_propiedad_usd", "valor_credito_usd", "control_2_pct",
            "resultado_control_2", "resultado_final", "motivo", "datos_faltantes",
            "observaciones",
        ],
        "additionalProperties": False,
    },
}


def construir_user_prompt(nombre_carpeta: str, ruta_o_id_drive: str, resumen_texto: str) -> str:
    with open(os.path.join(REPO_ROOT, "prompts", "user_prompt.md"), encoding="utf-8") as f:
        template = f.read()
    fecha_iso = datetime.now(timezone.utc).isoformat()
    # El template en user_prompt.md está documentado en Markdown; acá se arma
    # la versión real que se manda a la API con los valores reemplazados.
    return (
        "Analizá el siguiente legajo de crédito hipotecario y devolvé el JSON "
        "estructurado según el formato de salida definido en tu system prompt.\n\n"
        f"## Legajo: {nombre_carpeta}\n"
        f"## Fuente: {ruta_o_id_drive}\n"
        f"## Fecha de la corrida: {fecha_iso}\n\n"
        "### Legajo (texto extraído de Drive: Resumen Carpeta y, si existen, "
        "los comprobantes reales de la carpeta \"Ingresos\")\n\n"
        f"{resumen_texto}\n\n"
        "### Instrucciones específicas de esta corrida\n\n"
        "1. Extraé: número de crédito, jurisdicción, nombre del cliente, "
        "ingresos mensuales (propios y otros si los hay), cuota mensual "
        "(USD, ARS y tipo de cambio), valor de mercado de la propiedad y "
        "valor del crédito.\n"
        "2. Si el texto incluye comprobantes reales (facturación/recibos de "
        "sueldo) además del 'Resumen Carpeta', los comprobantes son la "
        "fuente de verdad — el resumen es solo una referencia rápida que "
        "puede tener errores de carga. Si un mes no coincide entre el "
        "resumen y el comprobante, usá el valor del comprobante y decilo "
        "explícitamente en `observaciones`.\n"
        "3. Pasá TODOS los meses de ingreso como lista a la herramienta (no "
        "promedies vos mismo) — la herramienta calcula el promedio, la "
        "volatilidad, y si algún mes es un valor atípico (`advertencias`). "
        "Si `advertencias` viene con contenido, copialo tal cual dentro de "
        "`observaciones` — no lo resumas ni lo omitas.\n"
        "4. Llamá a la herramienta `evaluar_legajo` con esos números "
        "(usando 'Crédito Aprobado', no 'Total Crédito con fee', para "
        "valor_credito_usd). Si alguno de los 4 datos no está en el texto, "
        "pasá `null` en ese campo — no inventes un número y no dejes de "
        "llamar a la herramienta.\n"
        "5. Completá el JSON de salida con el resultado de la herramienta y tu "
        "extracción de datos. Copiá `datos_faltantes` de la herramienta tal "
        "cual al campo `datos_faltantes` de tu salida, y explicá en "
        "`observaciones` qué falta y qué documentación haría falta pedir."
    )


def correr_agente(nombre_carpeta: str, ruta_o_id_drive: str, resumen_texto: str) -> dict:
    """Corre el agente real contra la API de Anthropic, en 2 llamadas:

    1. Llamada con tool_choice forzado a `evaluar_legajo` — el modelo NO
       puede responder con texto libre, tiene que extraer los 4 números y
       llamar a la herramienta determinista (gobierno: nunca calcula a mano).
    2. Llamada con output_config de esquema fijo, ya con el resultado de la
       herramienta en el historial, para obtener el JSON final estructurado.
    """
    client = anthropic.Anthropic()
    user_prompt = construir_user_prompt(nombre_carpeta, ruta_o_id_drive, resumen_texto)
    messages = [{"role": "user", "content": user_prompt}]

    call_1 = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        tools=[EVALUAR_LEGAJO_TOOL],
        tool_choice={"type": "tool", "name": "evaluar_legajo"},
        messages=messages,
    )

    tool_use_blocks = [b for b in call_1.content if b.type == "tool_use"]
    if not tool_use_blocks:
        raise RuntimeError(
            "El modelo no llamó a evaluar_legajo pese a tool_choice forzado "
            f"(stop_reason={call_1.stop_reason}) — no se puede confiar en un "
            "resultado sin el cálculo determinista."
        )

    messages.append({"role": "assistant", "content": call_1.content})
    tool_results = []
    for block in tool_use_blocks:
        try:
            resultado = evaluar_legajo(**block.input)
            content = json.dumps(resultado, ensure_ascii=False)
            is_error = False
        except Exception as exc:  # noqa: BLE001 - se reporta como tool_result de error
            content = f"Error al evaluar el legajo: {exc}"
            is_error = True
        tool_results.append({
            "type": "tool_result",
            "tool_use_id": block.id,
            "content": content,
            "is_error": is_error,
        })
    messages.append({"role": "user", "content": tool_results})

    # Segunda llamada: formato estructurado final sobre la conversación ya
    # resuelta (con el resultado de la herramienta adentro).
    call_2 = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        output_config={"format": OUTPUT_SCHEMA},
        messages=messages
        + [{"role": "user", "content": "Devolvé ahora el JSON final según el formato de salida."}],
    )
    texto = next(b.text for b in call_2.content if b.type == "text")

    uso = {
        "input_tokens": call_1.usage.input_tokens + call_2.usage.input_tokens,
        "output_tokens": call_1.usage.output_tokens + call_2.usage.output_tokens,
    }
    return {"salida": json.loads(texto), "uso_tokens": uso, "modelo": MODEL}




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drive-folder-id", required=True)
    parser.add_argument("--nombre-carpeta", default=None)
    parser.add_argument(
        "--excel-out",
        default=os.path.join(REPO_ROOT, "output", "legajos_maestro.xlsx"),
    )
    args = parser.parse_args()

    try:
        from drive_client import leer_legajo
    except ImportError as exc:
        print(
            "Faltan las dependencias de Google Drive. Instalá con:\n"
            "    pip install -r agente/requirements.txt\n"
            f"Detalle: {exc}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Leyendo legajo desde Drive (folder_id={args.drive_folder_id})...", file=sys.stderr)
    resumen_texto = leer_legajo(args.drive_folder_id)

    nombre_carpeta = args.nombre_carpeta or args.drive_folder_id
    resultado = correr_agente(nombre_carpeta, args.drive_folder_id, resumen_texto)
    salida = resultado["salida"]

    print(json.dumps(salida, indent=2, ensure_ascii=False))
    print(
        f"\nTokens: {resultado['uso_tokens']} — modelo: {resultado['modelo']}",
        file=sys.stderr,
    )

    agregar_legajo(args.excel_out, fila_excel(salida))
    print(f"Agregado a {args.excel_out}", file=sys.stderr)
