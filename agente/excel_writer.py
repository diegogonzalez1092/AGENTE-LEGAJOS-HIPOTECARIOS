"""
Herramienta real de escritura: agrega una fila al Excel maestro de legajos.

Es el segundo "conector real" del sistema (el primero es Google Drive, usado
para leer el resumen de cada legajo). Usa openpyxl y escribe directamente
sobre output/legajos_maestro.xlsx respetando las 14 columnas exigidas por la
consigna de negocio.
"""

from __future__ import annotations

import os
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter

COLUMNAS = [
    "Nro de crédito",
    "Jurisdicción",
    "Nombre y/o apellido del cliente",
    "Ingresos propios (ARS/mes)",
    "Otros ingresos (ARS/mes)",
    "Total ingresos (ARS/mes)",
    "1° cuota - USD",
    "1° cuota - TC",
    "1° cuota - $ (ARS)",
    "1er control (cuota/ingreso)",
    "Resultado 1er control",
    "Valor propiedad (USD)",
    "Valor crédito (USD)",
    "2do control (LTV)",
    "Resultado 2do control",
    "Resultado final",
]


def crear_o_abrir_maestro(path: str) -> Workbook:
    if os.path.exists(path):
        return load_workbook(path)
    wb = Workbook()
    ws = wb.active
    ws.title = "Legajos"
    ws.append(COLUMNAS)
    header_font = Font(name="Arial", bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    for col_idx, _ in enumerate(COLUMNAS, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[get_column_letter(col_idx)].width = 20
    ws.freeze_panes = "A2"
    return wb


def agregar_legajo(path: str, fila: dict) -> None:
    """fila: dict con las claves definidas en COLUMNAS (ver legajo_agent.py -> fila_excel())."""
    wb = crear_o_abrir_maestro(path)
    ws = wb["Legajos"]
    valores = [fila.get(col, "") for col in COLUMNAS]
    ws.append(valores)

    fila_idx = ws.max_row
    resultado = fila.get("Resultado final", "")
    fill = None
    if resultado == "ok credito aprobado":
        fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    elif resultado == "credito no aprobado":
        fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    if fill is not None:
        for col_idx in range(1, len(COLUMNAS) + 1):
            ws.cell(row=fila_idx, column=col_idx).fill = fill
        for col_idx in range(1, len(COLUMNAS) + 1):
            ws.cell(row=fila_idx, column=col_idx).font = Font(name="Arial")

    wb.save(path)
