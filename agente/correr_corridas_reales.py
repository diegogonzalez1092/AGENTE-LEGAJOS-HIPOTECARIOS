"""
Corre el agente real contra la API de Anthropic para los 3 legajos de
negocio y el caso de prueba "legajo incompleto", usando como entrada
exactamente el texto de `corridas/*/entrada.md` capturado desde Google
Drive (o, en el caso incompleto, construido a mano — ver ese entrada.md).

Cada corrida queda versionada: no sobreescribe la evidencia de corridas
anteriores. Cada ejecución se guarda completa en
`corridas/<caso>/runs/<timestamp>/` (salida.json, metadata.json, fecha.txt),
y además se actualizan `corridas/<caso>/salida.json` / `metadata.json` /
`fecha.txt` como un espejo de la corrida MÁS RECIENTE, para que el resto
del repo (README, output/legajos_maestro.xlsx) siga apuntando a un único
lugar sin tener que saber en qué carpeta de `runs/` quedó la última
ejecución (ver DECISIONES.md, Iteración 11 — sugerencia del agente
evaluador del grupo: "preservar cada corrida en una carpeta versionada en
vez de sobrescribir los artefactos anteriores").

output/legajos_maestro.xlsx solo se regenera a partir de los 3 legajos de
negocio reales (CORRIDAS) — el caso de prueba "incompleto" (CASOS_PRUEBA)
corre y guarda su evidencia igual, pero no es un legajo real y no entra al
Excel de negocio.

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

# Legajos de negocio reales — entran al Excel maestro.
CORRIDAS = ["corrida_01_perez", "corrida_02_gonzalez", "corrida_03_lopez"]

# Casos de prueba — corren y guardan evidencia igual, NO entran al Excel.
CASOS_PRUEBA = ["corrida_04_incompleto"]

# Precios Haiku 4.5 (ver ANALISIS_ECONOMICO.md) por millón de tokens.
PRECIO_INPUT_MTOK = 1.00
PRECIO_OUTPUT_MTOK = 5.00

NOTA_CANAL = (
    "Corrida ejecutada contra la API real de Anthropic (ver DECISIONES.md, "
    "Iteración 8). agente/tools.py::evaluar_legajo recibe la lista cruda de "
    "ingresos mensuales y promedia internamente — el LLM nunca hace ese "
    "cálculo (ver Iteración 9). Acepta `null` en cualquier campo para "
    "legajos incompletos sin que el modelo decida saltear la herramienta "
    "(ver Iteración 11)."
)


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


def guardar_corrida_versionada(carpeta: str, salida: dict, uso: dict, costo: float, nombre_carpeta: str) -> dict:
    """Escribe la corrida en runs/<timestamp>/ (sin tocar corridas previas) y
    actualiza el espejo de "última corrida" al nivel de corridas/<caso>/."""
    ahora = datetime.now(timezone.utc)
    run_id = ahora.strftime("%Y%m%dT%H%M%SZ")
    metadata = {
        "fecha_hora_utc": ahora.isoformat(),
        "run_id": run_id,
        "legajo": nombre_carpeta,
        "canal_de_ejecucion": f"API real de Anthropic ({MODEL}) vía agente/legajo_agent.py::correr_agente",
        "modelo": MODEL,
        "uso_tokens": uso,
        "costo_usd": round(costo, 6),
        "nota": NOTA_CANAL,
    }

    run_dir = os.path.join(carpeta, "runs", run_id)
    os.makedirs(run_dir, exist_ok=True)
    for nombre_archivo, contenido in [
        ("salida.json", json.dumps(salida, indent=2, ensure_ascii=False) + "\n"),
        ("metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False) + "\n"),
        ("fecha.txt", metadata["fecha_hora_utc"] + "\n"),
    ]:
        with open(os.path.join(run_dir, nombre_archivo), "w", encoding="utf-8") as f:
            f.write(contenido)

    # Espejo de "última corrida" al nivel de corridas/<caso>/ — no reemplaza
    # runs/, solo facilita encontrar el resultado más reciente sin recorrer
    # subcarpetas con timestamp.
    for nombre_archivo, contenido in [
        ("salida.json", json.dumps(salida, indent=2, ensure_ascii=False) + "\n"),
        ("metadata.json", json.dumps(metadata, indent=2, ensure_ascii=False) + "\n"),
        ("fecha.txt", metadata["fecha_hora_utc"] + "\n"),
    ]:
        with open(os.path.join(carpeta, nombre_archivo), "w", encoding="utf-8") as f:
            f.write(contenido)

    return metadata


def correr_caso(nombre: str) -> tuple[dict, dict, float]:
    carpeta = os.path.join(CORRIDAS_DIR, nombre)
    nombre_carpeta, fuente, resumen_texto = parsear_entrada(os.path.join(carpeta, "entrada.md"))

    print(f"--- Corriendo {nombre} ({nombre_carpeta}) contra la API real ({MODEL}) ---")
    resultado = correr_agente(nombre_carpeta, fuente, resumen_texto)
    salida = resultado["salida"]
    uso = resultado["uso_tokens"]
    costo = costo_usd(uso)

    metadata = guardar_corrida_versionada(carpeta, salida, uso, costo, nombre_carpeta)
    print(
        f"    -> {salida.get('cliente')}: {salida.get('resultado_final')} "
        f"(tokens in={uso['input_tokens']} out={uso['output_tokens']}, "
        f"costo=USD {costo:.6f}, run_id={metadata['run_id']})"
    )
    return salida, uso, costo


if __name__ == "__main__":
    if os.path.exists(EXCEL_OUT):
        os.remove(EXCEL_OUT)

    costo_total = 0.0
    tokens_totales = {"input_tokens": 0, "output_tokens": 0}
    n_corridas = 0

    for nombre in CORRIDAS:
        salida, uso, costo = correr_caso(nombre)
        costo_total += costo
        tokens_totales["input_tokens"] += uso["input_tokens"]
        tokens_totales["output_tokens"] += uso["output_tokens"]
        n_corridas += 1
        agregar_legajo(EXCEL_OUT, fila_excel(salida))

    print("\n=== Resumen de costo real (legajos de negocio) ===")
    print(f"Tokens de entrada totales: {tokens_totales['input_tokens']}")
    print(f"Tokens de salida totales: {tokens_totales['output_tokens']}")
    print(f"Costo total real: USD {costo_total:.6f}")
    print(f"Costo promedio por corrida: USD {costo_total / n_corridas:.6f}")
    print(f"\nExcel maestro regenerado en: {EXCEL_OUT}")

    print("\n=== Casos de prueba (no entran al Excel) ===")
    for nombre in CASOS_PRUEBA:
        correr_caso(nombre)
