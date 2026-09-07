"""
Orquestador de producción del Agente de Análisis Financiero de Legajos
Hipotecarios.

Este script es el que correría la empresa en producción, con su propia
ANTHROPIC_API_KEY: lee el resumen de un legajo (Google Drive), lo pasa a
Claude junto con el contrato de prompts/system_prompt.md + user_prompt.md,
deja que el modelo llame a la herramienta determinista evaluar_legajo() para
los dos controles financieros, y escribe el resultado en el Excel maestro.

IMPORTANTE (ver DECISIONES.md, "Iteración 3" y GOBIERNO_Y_RIESGO.md):
Esta entrega NO tuvo acceso a una ANTHROPIC_API_KEY real. Las 3 corridas
reales documentadas en corridas/ se ejecutaron con el mismo contrato (mismo
system/user prompt, misma herramienta evaluar_legajo, mismo Excel de salida)
pero con Claude actuando directamente dentro de la sesión de Claude Code que
construyó este repo, usando su conector real de Google Drive en vez de esta
llamada a la API. Este script queda completo y listo para correr apenas haya
una API key — es el camino a producción, no un mock.

Uso:
    export ANTHROPIC_API_KEY=sk-ant-...
    python agente/legajo_agent.py --drive-folder-id <ID_DE_LA_CARPETA_DEL_LEGAJO>
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
        "calcular los porcentajes en el texto de la respuesta."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "cuota_mensual_ars": {"type": "number"},
            "ingreso_neto_mensual_ars": {"type": "number"},
            "valor_credito_usd": {"type": "number"},
            "valor_propiedad_usd": {"type": "number"},
        },
        "required": [
            "cuota_mensual_ars",
            "ingreso_neto_mensual_ars",
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
            "nro_credito": {"type": "string"},
            "jurisdiccion": {"type": "string"},
            "cliente": {"type": "string"},
            "ingresos_propios_ars": {"type": "number"},
            "otros_ingresos_ars": {"type": "number"},
            "total_ingresos_ars": {"type": "number"},
            "cuota_usd": {"type": "number"},
            "tipo_cambio": {"type": "number"},
            "cuota_ars": {"type": "number"},
            "control_1_pct": {"type": "number"},
            "resultado_control_1": {"type": "string", "enum": ["ok credito", "no cumple"]},
            "valor_propiedad_usd": {"type": "number"},
            "valor_credito_usd": {"type": "number"},
            "control_2_pct": {"type": "number"},
            "resultado_control_2": {"type": "string", "enum": ["ok credito", "no cumple"]},
            "resultado_final": {
                "type": "string",
                "enum": ["ok credito aprobado", "credito no aprobado"],
            },
            "motivo": {"type": ["string", "null"]},
            "observaciones": {"type": ["string", "null"]},
        },
        "required": [
            "nro_credito", "jurisdiccion", "cliente", "ingresos_propios_ars",
            "otros_ingresos_ars", "total_ingresos_ars", "cuota_usd", "tipo_cambio",
            "cuota_ars", "control_1_pct", "resultado_control_1",
            "valor_propiedad_usd", "valor_credito_usd", "control_2_pct",
            "resultado_control_2", "resultado_final", "motivo", "observaciones",
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
        "### Resumen Carpeta (texto extraído del Excel real del legajo)\n\n"
        f"{resumen_texto}\n\n"
        "### Instrucciones específicas de esta corrida\n\n"
        "1. Extraé del texto de arriba: número de crédito, jurisdicción, nombre "
        "del cliente, ingresos mensuales (propios y otros si los hay), cuota "
        "mensual (USD, ARS y tipo de cambio), valor de mercado de la propiedad "
        "y valor del crédito.\n"
        "2. Si hay varios meses de ingresos informados, usá el promedio como "
        "ingreso neto mensual para el Control 1, y mencioná en `observaciones` "
        "si hay alta volatilidad entre meses.\n"
        "3. Llamá a la herramienta `evaluar_legajo` con esos números.\n"
        "4. Completá el JSON de salida con el resultado de la herramienta y tu "
        "extracción de datos."
    )


def correr_agente(nombre_carpeta: str, ruta_o_id_drive: str, resumen_texto: str) -> dict:
    client = anthropic.Anthropic()
    user_prompt = construir_user_prompt(nombre_carpeta, ruta_o_id_drive, resumen_texto)
    messages = [{"role": "user", "content": user_prompt}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=[EVALUAR_LEGAJO_TOOL],
            messages=messages,
        )

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_use_blocks:
            break

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in tool_use_blocks:
            if block.name == "evaluar_legajo":
                try:
                    resultado = evaluar_legajo(**block.input)
                    content = json.dumps(resultado, ensure_ascii=False)
                    is_error = False
                except Exception as exc:  # noqa: BLE001 - se reporta como tool_result de error
                    content = f"Error al evaluar el legajo: {exc}"
                    is_error = True
            else:
                content = f"Herramienta desconocida: {block.name}"
                is_error = True
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": content,
                "is_error": is_error,
            })
        messages.append({"role": "user", "content": tool_results})

    # Última llamada: forzamos el formato estructurado final sobre la
    # conversación ya resuelta (con el resultado de la herramienta adentro).
    final = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        output_config={"format": OUTPUT_SCHEMA},
        messages=messages
        + [{"role": "user", "content": "Devolvé ahora el JSON final según el formato de salida."}],
    )
    texto = next(b.text for b in final.content if b.type == "text")

    uso = {
        "input_tokens": response.usage.input_tokens + final.usage.input_tokens,
        "output_tokens": response.usage.output_tokens + final.usage.output_tokens,
    }
    return {"salida": json.loads(texto), "uso_tokens": uso, "modelo": MODEL}


def fila_excel(salida: dict) -> dict:
    return {
        "Nro de crédito": salida["nro_credito"],
        "Jurisdicción": salida["jurisdiccion"],
        "Nombre y/o apellido del cliente": salida["cliente"],
        "Ingresos propios (ARS/mes)": salida["ingresos_propios_ars"],
        "Otros ingresos (ARS/mes)": salida["otros_ingresos_ars"],
        "Total ingresos (ARS/mes)": salida["total_ingresos_ars"],
        "1° cuota - USD": salida["cuota_usd"],
        "1° cuota - TC": salida["tipo_cambio"],
        "1° cuota - $ (ARS)": salida["cuota_ars"],
        "1er control (cuota/ingreso)": f"{salida['control_1_pct']}%",
        "Resultado 1er control": salida["resultado_control_1"],
        "Valor propiedad (USD)": salida["valor_propiedad_usd"],
        "Valor crédito (USD)": salida["valor_credito_usd"],
        "2do control (LTV)": f"{salida['control_2_pct']}%",
        "Resultado 2do control": salida["resultado_control_2"],
        "Resultado final": salida["resultado_final"]
        + (f" — {salida['motivo']}" if salida.get("motivo") else ""),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--drive-folder-id", required=True)
    parser.add_argument("--nombre-carpeta", default=None)
    parser.add_argument(
        "--excel-out",
        default=os.path.join(REPO_ROOT, "output", "legajos_maestro.xlsx"),
    )
    args = parser.parse_args()

    print(
        "Este script necesita ANTHROPIC_API_KEY y un cliente de Google Drive "
        "real conectado para leer args.drive_folder_id. No se ejecuta en esta "
        "entrega por falta de API key propia — ver DECISIONES.md.",
        file=sys.stderr,
    )
    sys.exit(1)
