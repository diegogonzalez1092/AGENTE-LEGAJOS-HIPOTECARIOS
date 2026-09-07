"""
Genera output/legajos_maestro.xlsx a partir de las 3 salidas estructuradas
reales en corridas/*/salida.json. Es el script que un tercero puede correr
para reconstruir el Excel maestro sin necesidad de ANTHROPIC_API_KEY.

Uso: python agente/generar_excel_maestro.py
"""

from __future__ import annotations

import json
import os

from excel_writer import agregar_legajo

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
CORRIDAS_DIR = os.path.join(REPO_ROOT, "corridas")
EXCEL_OUT = os.path.join(REPO_ROOT, "output", "legajos_maestro.xlsx")

CORRIDAS = ["corrida_01_perez", "corrida_02_gonzalez", "corrida_03_lopez"]


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
    if os.path.exists(EXCEL_OUT):
        os.remove(EXCEL_OUT)  # regenerar desde cero para que sea reproducible
    for nombre in CORRIDAS:
        with open(os.path.join(CORRIDAS_DIR, nombre, "salida.json"), encoding="utf-8") as f:
            salida = json.load(f)
        agregar_legajo(EXCEL_OUT, fila_excel(salida))
        print(f"Agregado: {salida['cliente']} -> {salida['resultado_final']}")
    print(f"\nExcel maestro generado en: {EXCEL_OUT}")
