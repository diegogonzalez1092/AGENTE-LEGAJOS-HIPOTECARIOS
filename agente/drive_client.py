"""
Cliente real de Google Drive para el agente de legajos hipotecarios.

Implementado con la librería oficial de Google (`google-api-python-client` +
`google-auth`), API v3, alcance de solo lectura
(`drive.readonly`). No es un mock ni una simulación: las llamadas siguen
exactamente la referencia pública de la API
(https://developers.google.com/drive/api/v3/reference/files).

IMPORTANTE (ver DECISIONES.md, Iteración 11): este módulo no se pudo probar
de punta a punta en el entorno de esta entrega porque no hay credenciales de
una cuenta de servicio de Google Cloud disponibles acá. Lo que sí se probó:
que el archivo importa y compila sin errores, y que `_xlsx_a_texto` produce
el mismo formato (filas separadas por coma) que el conector MCP de Google
Drive de Claude Code, comparado a mano contra `corridas/*/entrada.md`. La
lectura real de Drive para las 3 corridas del repo se hizo con ese conector,
no con este módulo — ver `corridas/README.md`. Este es el camino real de
producción, listo para correr en cuanto haya una cuenta de servicio.

Setup para producción:
1. Crear (o usar) un proyecto en Google Cloud Console y habilitar la
   "Google Drive API".
2. Crear una cuenta de servicio (IAM & Admin → Service Accounts) y
   descargar su JSON de credenciales.
3. Compartir la carpeta de Drive de legajos con el email de la cuenta de
   servicio (rol Viewer alcanza — es de solo lectura, ver
   GOBIERNO_Y_RIESGO.md, principio de mínimo privilegio).
4. `export GOOGLE_APPLICATION_CREDENTIALS=/ruta/al/credenciales.json`
"""

from __future__ import annotations

import io
import os
import re
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import openpyxl

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
FOLDER_MIME = "application/vnd.google-apps.folder"
PDF_MIME = "application/pdf"

_servicio = None  # cacheado por proceso — evita re-autenticar en cada llamada


def _cliente():
    global _servicio
    if _servicio is not None:
        return _servicio
    ruta_credenciales = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not ruta_credenciales:
        raise RuntimeError(
            "Falta GOOGLE_APPLICATION_CREDENTIALS (ruta al JSON de la cuenta "
            "de servicio de Google Cloud). Ver el docstring de este módulo "
            "para el setup completo."
        )
    credenciales = service_account.Credentials.from_service_account_file(
        ruta_credenciales, scopes=SCOPES
    )
    _servicio = build("drive", "v3", credentials=credenciales)
    return _servicio


def listar_archivos(folder_id: str) -> list[dict]:
    """Lista los archivos y subcarpetas directos de una carpeta de Drive."""
    servicio = _cliente()
    resultados: list[dict] = []
    page_token = None
    while True:
        respuesta = (
            servicio.files()
            .list(
                q=f"'{folder_id}' in parents and trashed = false",
                fields="nextPageToken, files(id, name, mimeType)",
                pageToken=page_token,
            )
            .execute()
        )
        resultados.extend(respuesta.get("files", []))
        page_token = respuesta.get("nextPageToken")
        if not page_token:
            break
    return resultados


def _descargar_bytes(file_id: str) -> bytes:
    servicio = _cliente()
    request = servicio.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    listo = False
    while not listo:
        _, listo = downloader.next_chunk()
    return buffer.getvalue()


def _xlsx_a_texto(contenido: bytes) -> str:
    """Convierte un .xlsx real (no Google Sheets) a texto plano por filas,
    con las celdas separadas por coma — el mismo formato aproximado que
    devolvía el conector de Drive usado en las 3 corridas reales (ver
    `corridas/*/entrada.md` para el formato de referencia)."""
    libro = openpyxl.load_workbook(io.BytesIO(contenido), data_only=True)
    lineas = []
    for hoja in libro.worksheets:
        for fila in hoja.iter_rows(values_only=True):
            celdas = ["" if v is None else str(v) for v in fila]
            if any(celdas):
                lineas.append(",".join(celdas))
    return "\n".join(lineas)


def _pdf_a_texto(contenido: bytes) -> str:
    """Extracción de texto de PDF (recibos de sueldo). Requiere `pypdf`."""
    from pypdf import PdfReader

    lector = PdfReader(io.BytesIO(contenido))
    return "\n".join(pagina.extract_text() or "" for pagina in lector.pages)


def leer_archivo_como_texto(file_id: str, mime_type: str) -> str:
    contenido = _descargar_bytes(file_id)
    if mime_type == XLSX_MIME:
        return _xlsx_a_texto(contenido)
    if mime_type == PDF_MIME:
        return _pdf_a_texto(contenido)
    return contenido.decode("utf-8", errors="replace")


def leer_legajo(folder_id: str) -> str:
    """Lee el "Resumen Carpeta" de un legajo y, si existe una subcarpeta
    "Ingresos", también sus comprobantes reales — devuelve todo concatenado
    como el `resumen_texto` que espera `legajo_agent.correr_agente` (ver
    DECISIONES.md, Iteración 10, sobre por qué los comprobantes reales
    importan tanto como el resumen)."""
    archivos = listar_archivos(folder_id)

    partes = []
    carpeta_ingresos_id: Optional[str] = None

    for archivo in archivos:
        if archivo["mimeType"] == FOLDER_MIME:
            if archivo["name"].strip().lower() == "ingresos":
                carpeta_ingresos_id = archivo["id"]
            continue
        if archivo["mimeType"] == XLSX_MIME:
            texto = leer_archivo_como_texto(archivo["id"], archivo["mimeType"])
            partes.append(f"## Resumen Carpeta ({archivo['name']})\n\n```\n{texto}\n```")

    if carpeta_ingresos_id:
        comprobantes = [
            a for a in listar_archivos(carpeta_ingresos_id) if a["mimeType"] != FOLDER_MIME
        ]
        if comprobantes:
            partes.append('## Comprobantes reales (carpeta "Ingresos")\n')
            for comprobante in sorted(comprobantes, key=lambda a: a["name"]):
                texto = leer_archivo_como_texto(comprobante["id"], comprobante["mimeType"])
                partes.append(f"### {comprobante['name']}\n\n```\n{texto}\n```")

    if not partes:
        raise RuntimeError(f"No se encontró ningún .xlsx de resumen en la carpeta {folder_id}")

    return "\n\n".join(partes)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Uso: python drive_client.py <ID_DE_LA_CARPETA_DEL_LEGAJO>", file=sys.stderr)
        raise SystemExit(1)
    print(leer_legajo(sys.argv[1]))
