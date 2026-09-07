"""
Re-corre las 3 corridas reales contra la API de Anthropic (ya no dentro de la
sesión de Claude Code, sino con `legajo_agent.correr_agente()` de verdad),
usando como entrada exactamente el mismo texto de `corridas/*/entrada.md`
capturado la primera vez desde Google Drive.

Sobrescribe `corridas/*/salida.json` y `corridas/*/metadata.json` con el
resultado y el `usage`/costo REALES de esta corrida, y regenera
output/legajos_maestro.xlsx a partir de esas salidas nuevas.

Uso:
    export ANTHROPIC_API_KEY=sk-ant-...
    python agente/correr_corridas_reales.py
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone

from legajo_agent import correr_agente, MODEL
from generar_excel_maestro import fila_excel
from excel_writer import agregar_legajo

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
CORRIDAS_DIR = os.path.join(REPO_ROOT, "corridas")
EXCEL_OUT = os.path.join(REPO_ROOT, "output", "legajos_maestro.xlsx")

CORRIDAS = ["corrida_01_perez", "corrida_02_gonzalez", "corrida_03_lopez"]

# Precios Haiku 4.5 (ver ANALISIS_ECONOMICO.md) por millón de tokens.
PRECIO_INPUT_MTOK = 1.00
PRECIO_OUTPUT_MTOK = 5.00


def parsear_entrada(path_entrada_md: str) -> tuple[str, str, str]:
    """Extrae (nombre_carpeta, fuente, resumen_texto) de un entrada.md.

    `resumen_texto` es TODO lo que hay desde el primer encabezado `## ` hasta
    el final del archivo — no solo el primer bloque de código. Esto importa
    para legajos como Lopez, donde entrada.md trae, además del "Resumen
    Carpeta", una sección de hallazgo (la discrepancia contra los
    comprobantes reales) y una sección de comprobantes reales: el agente
    necesita ver las tres para poder priorizar el comprobante sobre el
    resumen (ver DECISIONES.md, Iteración 10).
    """
    with open(path_entrada_md, encoding="utf-8") as f:
        texto = f.read()

    nombre_match = re.search(r"^# Corrida \d+ — (.+)$", texto, re.MULTILINE)
    nombre_carpeta = nombre_match.group(1).strip() if nombre_match else "Legajo"

    fuente_match = re.search(r"\*\*Archivo fuente[^*]*\*\*: (.+)$", texto, re.MULTILINE)
    fuente = fuente_match.group(1).strip() if fuente_match else path_entrada_md

    cuerpo_match = re.search(r"^## .*$", texto, re.MULTILINE)
    if not cuerpo_match:
        raise ValueError(f"No se encontró ningún encabezado '## ' en {path_entrada_md}")
    resumen_texto = texto[cuerpo_match.start():].strip()

    return nombre_carpeta, fuente, resumen_texto


def costo_usd(uso_tokens: dict) -> float:
    return (
        uso_tokens["input_tokens"] / 1_000_000 * PRECIO_INPUT_MTOK
        + uso_tokens["output_tokens"] / 1_000_000 * PRECIO_OUTPUT_MTOK
    )


if __name__ == "__main__":
    if os.path.exists(EXCEL_OUT):
        os.remove(EXCEL_OUT)

    costo_total = 0.0
    tokens_totales = {"input_tokens": 0, "output_tokens": 0}

    for nombre in CORRIDAS:
        carpeta = os.path.join(CORRIDAS_DIR, nombre)
        nombre_carpeta, fuente, resumen_texto = parsear_entrada(os.path.join(carpeta, "entrada.md"))

        print(f"--- Corriendo {nombre} ({nombre_carpeta}) contra la API real ({MODEL}) ---")
        resultado = correr_agente(nombre_carpeta, fuente, resumen_texto)
        salida = resultado["salida"]
        uso = resultado["uso_tokens"]
        costo = costo_usd(uso)
        costo_total += costo
        tokens_totales["input_tokens"] += uso["input_tokens"]
        tokens_totales["output_tokens"] += uso["output_tokens"]

        with open(os.path.join(carpeta, "salida.json"), "w", encoding="utf-8") as f:
            json.dump(salida, f, indent=2, ensure_ascii=False)
            f.write("\n")

        metadata = {
            "fecha_hora_utc": datetime.now(timezone.utc).isoformat(),
            "legajo": nombre_carpeta,
            "canal_de_ejecucion": f"API real de Anthropic ({MODEL}) vía agente/legajo_agent.py::correr_agente",
            "modelo": MODEL,
            "uso_tokens": uso,
            "costo_usd": round(costo, 6),
            "nota": (
                "Corrida ejecutada contra la API real de Anthropic (ver "
                "DECISIONES.md, Iteración 8). agente/tools.py::evaluar_legajo "
                "recibe la lista cruda de ingresos mensuales y promedia "
                "internamente — el LLM nunca hace ese cálculo (ver "
                "DECISIONES.md, Iteración 9, sobre el bug que motivó este "
                "diseño)."
            ),
        }
        with open(os.path.join(carpeta, "metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            f.write("\n")

        # Requisito de formato de la consigna: corridas/ debe traer entrada,
        # salida Y fecha como cosas identificables por separado — fecha.txt
        # es la versión mínima de eso (además de repetirse en metadata.json
        # y en el encabezado de entrada.md).
        with open(os.path.join(carpeta, "fecha.txt"), "w", encoding="utf-8") as f:
            f.write(metadata["fecha_hora_utc"] + "\n")

        agregar_legajo(EXCEL_OUT, fila_excel(salida))
        print(
            f"    -> {salida['cliente']}: {salida['resultado_final']} "
            f"(tokens in={uso['input_tokens']} out={uso['output_tokens']}, "
            f"costo=USD {costo:.6f})"
        )

    print("\n=== Resumen de costo real (3 corridas) ===")
    print(f"Tokens de entrada totales: {tokens_totales['input_tokens']}")
    print(f"Tokens de salida totales: {tokens_totales['output_tokens']}")
    print(f"Costo total real: USD {costo_total:.6f}")
    print(f"Costo promedio por corrida: USD {costo_total / len(CORRIDAS):.6f}")
    print(f"\nExcel maestro regenerado en: {EXCEL_OUT}")
