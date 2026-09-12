"""
Lectura de .xlsx compartida entre el cliente de Google Drive
(`drive_client.py`) y la carga manual de archivo en la app web (`app.py`) —
mismo formato de texto en los dos casos, sin duplicar código ni forzar que
la app web dependa de las librerías de Google (`google-api-python-client`,
`google-auth`) solo para leer un Excel que el usuario subió a mano.
"""

from __future__ import annotations

import io

import openpyxl


def xlsx_a_texto(contenido: bytes) -> str:
    """Convierte un .xlsx real (no Google Sheets) a texto plano por filas,
    con las celdas separadas por coma — el mismo formato que devolvía el
    conector de Drive usado en las corridas reales (ver
    `corridas/*/entrada.md` para el formato de referencia)."""
    libro = openpyxl.load_workbook(io.BytesIO(contenido), data_only=True)
    lineas = []
    for hoja in libro.worksheets:
        for fila in hoja.iter_rows(values_only=True):
            celdas = ["" if v is None else str(v) for v in fila]
            if any(celdas):
                lineas.append(",".join(celdas))
    return "\n".join(lineas)
