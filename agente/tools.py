"""
Herramientas deterministas del agente de análisis financiero de legajos hipotecarios.

Estas funciones NO usan el LLM: son cálculos aritméticos verificables, expuestos
al modelo como tool calls (ver agente/legajo_agent.py) para que la decisión de
aprobación nunca dependa de que Claude "haga la cuenta bien" en texto libre.
Esta separación (LLM extrae y redacta, código calcula) es una decisión de
gobierno documentada en DECISIONES.md y GOBIERNO_Y_RIESGO.md.

IMPORTANTE (ver DECISIONES.md, Iteración 9): la primera versión de esta
función recibía `ingreso_neto_mensual_ars` ya promediado — es decir, le
pedía al LLM que calculara el promedio de varios meses de ingreso ANTES de
llamar a la herramienta. Al correr el agente contra la API real, el promedio
que calculó el modelo para el legajo Lopez vino mal (ARS 2.038.609 en vez de
ARS 1.702.510), lo que cambió el resultado del Control 1. La función recibe
ahora la LISTA cruda de ingresos mensuales y el promedio también lo calcula
este código, no el LLM — cerrando el hueco real que dejó pasar ese bug.

IMPORTANTE #2 (ver DECISIONES.md, Iteración 10): el usuario notó, mirando el
Excel del legajo Lopez, que el ingreso de agosto no coincide con los
comprobantes reales de facturación (la carpeta "Ingresos" de cada legajo en
Drive) — y que, además de no coincidir, ese mes es un valor atípico
extremo frente al resto (una sola factura de casi 4-25x los demás meses a un
único cliente). `promediar_ingresos` ahora detecta esos meses atípicos
(> 3× la mediana del resto) y los devuelve en `outliers`, para que
`evaluar_legajo` los reporte como una advertencia de integridad de datos
—independiente de si los controles 1 y 2 aprueban o no—, en vez de
promediarlos como si fueran ingreso recurrente normal sin más.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, asdict
from typing import Optional, Sequence

LIMITE_CUOTA_INGRESO = 0.40  # Requisito de negocio: la cuota no puede superar el 40% del ingreso neto
LIMITE_LTV = 0.35  # Requisito de negocio: el crédito no puede superar el 35% del valor de mercado del inmueble


@dataclass
class ResultadoControl:
    nombre: str
    valor_medido: float  # razón calculada, ej. 0.273 = 27.3%
    limite: float
    aprueba: bool

    def to_dict(self) -> dict:
        d = asdict(self)
        d["valor_medido_pct"] = round(self.valor_medido * 100, 1)
        d["limite_pct"] = round(self.limite * 100, 1)
        return d


UMBRAL_OUTLIER_X_MEDIANA = 3.0  # un mes > 3x la mediana no se trata como ingreso recurrente sin más


def promediar_ingresos(ingresos_mensuales_ars: Sequence[float]) -> dict:
    """Promedio, volatilidad y detección de meses atípicos de una lista de
    ingresos mensuales — cálculo determinista, nunca a cargo del LLM (ver
    nota de módulo).

    Un mes "atípico" (> 3x la mediana de todos los meses informados) no se
    excluye automáticamente del promedio — la regla de negocio de la
    empresa sigue siendo "promedio de los meses informados" — pero se
    reporta aparte para que quede visible: un ingreso que no se parece a
    los demás meses del mismo cliente necesita verificación documental
    antes de tratarse como ingreso recurrente (ver DECISIONES.md,
    Iteración 10, y GOBIERNO_Y_RIESGO.md).
    """
    if not ingresos_mensuales_ars:
        raise ValueError("ingresos_mensuales_ars no puede estar vacío")
    valores = [float(v) for v in ingresos_mensuales_ars]
    promedio = sum(valores) / len(valores)
    minimo, maximo = min(valores), max(valores)
    variacion_pct = ((maximo - minimo) / minimo * 100) if minimo > 0 else float("inf")
    mediana = statistics.median(valores)
    outliers = [
        {"valor": v, "veces_mediana": round(v / mediana, 1)}
        for v in valores
        if mediana > 0 and v > UMBRAL_OUTLIER_X_MEDIANA * mediana
    ]
    return {
        "promedio": promedio,
        "minimo": minimo,
        "maximo": maximo,
        "mediana": mediana,
        "variacion_pct": round(variacion_pct, 1),
        "alta_volatilidad": variacion_pct > 100,
        "outliers": outliers,
    }


def evaluar_control_cuota_ingreso(cuota_mensual_ars: float, ingreso_neto_mensual_ars: float) -> ResultadoControl:
    """Control 1: la cuota mensual del crédito no puede superar el 40% del ingreso neto del cliente."""
    if ingreso_neto_mensual_ars <= 0:
        raise ValueError("ingreso_neto_mensual_ars debe ser mayor a 0")
    razon = cuota_mensual_ars / ingreso_neto_mensual_ars
    return ResultadoControl(
        nombre="cuota_ingreso",
        valor_medido=razon,
        limite=LIMITE_CUOTA_INGRESO,
        aprueba=razon <= LIMITE_CUOTA_INGRESO,
    )


def evaluar_control_ltv(valor_credito_usd: float, valor_propiedad_usd: float) -> ResultadoControl:
    """Control 2 (LTV): el crédito no puede superar el 35% del valor de mercado del inmueble."""
    if valor_propiedad_usd <= 0:
        raise ValueError("valor_propiedad_usd debe ser mayor a 0")
    razon = valor_credito_usd / valor_propiedad_usd
    return ResultadoControl(
        nombre="ltv",
        valor_medido=razon,
        limite=LIMITE_LTV,
        aprueba=razon <= LIMITE_LTV,
    )


def evaluar_legajo(
    cuota_mensual_ars: Optional[float],
    ingresos_mensuales_ars: Optional[Sequence[float]],
    valor_credito_usd: Optional[float],
    valor_propiedad_usd: Optional[float],
) -> dict:
    """Aplica los dos controles duros y arma la decisión final + motivo si corresponde.

    Esta es la función expuesta como tool al modelo (ver agente/legajo_agent.py).
    El LLM pasa la lista cruda de ingresos mensuales tal como la extrajo del
    legajo — el promedio, igual que los dos controles, lo calcula este código.

    Legajos incompletos (ver DECISIONES.md, Iteración 11): cualquiera de los
    4 parámetros puede venir en `None` (o la lista de ingresos, vacía). La
    herramienta se sigue llamando SIEMPRE — el `tool_choice` forzado en
    `agente/legajo_agent.py` no cambia — pero acá adentro, de forma
    determinista, se detecta qué falta y se evalúa cada control por
    separado: si a un control le faltan sus datos, ese control queda en
    `None` con el motivo en `datos_faltantes`, en vez de forzar al LLM a
    inventar un número o a decidir por su cuenta si llama a la herramienta
    o no.
    """
    datos_faltantes = []

    ingresos = None
    control_1 = None
    if cuota_mensual_ars is None:
        datos_faltantes.append("cuota_mensual_ars")
    if not ingresos_mensuales_ars:
        datos_faltantes.append("ingresos_mensuales_ars")
    if cuota_mensual_ars is not None and ingresos_mensuales_ars:
        ingresos = promediar_ingresos(ingresos_mensuales_ars)
        control_1 = evaluar_control_cuota_ingreso(cuota_mensual_ars, ingresos["promedio"])

    control_2 = None
    if valor_credito_usd is None:
        datos_faltantes.append("valor_credito_usd")
    if valor_propiedad_usd is None:
        datos_faltantes.append("valor_propiedad_usd")
    if valor_credito_usd is not None and valor_propiedad_usd is not None:
        control_2 = evaluar_control_ltv(valor_credito_usd, valor_propiedad_usd)

    advertencias = []
    if ingresos is not None:
        for outlier in ingresos["outliers"]:
            advertencias.append(
                f"Ingreso mensual de ARS {outlier['valor']:,.0f} es {outlier['veces_mediana']}x "
                f"la mediana del resto de los meses informados — no debe tratarse como ingreso "
                f"recurrente sin verificar el comprobante que lo respalda (posible pago no "
                f"recurrente o error de carga)."
            )

    if control_1 is None or control_2 is None:
        return {
            "ingresos": ingresos,
            "control_1_cuota_ingreso": control_1.to_dict() if control_1 else None,
            "control_2_ltv": control_2.to_dict() if control_2 else None,
            "resultado_final": "no evaluable",
            "motivo": None,
            "advertencias": advertencias,
            "datos_faltantes": datos_faltantes,
        }

    motivos = []
    if not control_1.aprueba:
        motivos.append(
            f"Relación cuota/ingreso de {control_1.valor_medido * 100:.1f}% "
            f"supera el límite de {LIMITE_CUOTA_INGRESO * 100:.0f}%"
        )
    if not control_2.aprueba:
        motivos.append(
            f"LTV de {control_2.valor_medido * 100:.1f}% supera el límite de {LIMITE_LTV * 100:.0f}%"
        )

    aprobado = control_1.aprueba and control_2.aprueba

    return {
        "ingresos": ingresos,
        "control_1_cuota_ingreso": control_1.to_dict(),
        "control_2_ltv": control_2.to_dict(),
        "resultado_final": "ok credito aprobado" if aprobado else "credito no aprobado",
        "motivo": None if aprobado else "; ".join(motivos),
        "advertencias": advertencias,  # se reportan aprobado o no — ver evaluar_control_cuota_ingreso
        "datos_faltantes": datos_faltantes,  # vacío cuando el legajo está completo
    }


if __name__ == "__main__":
    import json

    # Los tres legajos reales de la carpeta de Drive "Trabajo Final - Creación
    # agentes de IA". Ver corridas/ para el detalle de extracción por legajo.
    # Control 2 usa siempre "Crédito Aprobado", sin fee (DECISIONES.md,
    # Iteración 9). Los ingresos mensuales de Perez y Gonzalez están
    # verificados contra los comprobantes reales de la carpeta "Ingresos" de
    # cada legajo y coinciden (Gonzalez, exacto; Perez, diferencias <1.5%
    # atribuibles a redondeo de recibo de sueldo). Los de Lopez son los
    # comprobantes reales de facturación, NO el "Resumen Carpeta" — julio y
    # agosto del resumen no coinciden con los comprobantes (ver DECISIONES.md,
    # Iteración 10).
    casos = {
        "Perez": dict(
            cuota_mensual_ars=739378.83,
            ingresos_mensuales_ars=[2587123, 2809243, 2726198],
            valor_credito_usd=20000,
            valor_propiedad_usd=98000,
        ),
        "Gonzalez": dict(
            cuota_mensual_ars=1066974.90,
            ingresos_mensuales_ars=[2758900, 2150300, 2945600, 3029535, 2635650, 2739680],
            valor_credito_usd=33000,
            valor_propiedad_usd=120000,
        ),
        "Lopez": dict(
            cuota_mensual_ars=735475.99,
            # Comprobantes reales (03 a 08-2026 Ventas.xlsx): el resumen decía
            # 1.741.680 en julio (copiado de junio) y 6.000.000 en agosto —
            # los comprobantes reales son 1.654.750 y 6.500.000.
            ingresos_mensuales_ars=[282505, 70000, 379192, 1741680, 1654750, 6500000],
            valor_credito_usd=21452,
            valor_propiedad_usd=53000,
        ),
        # Legajo incompleto sintético (ver corridas/corrida_04_incompleto y
        # DECISIONES.md, Iteración 11): no trae valor de mercado de la
        # propiedad. Control 1 sí se puede evaluar; Control 2, no.
        "Incompleto (sin valor de propiedad)": dict(
            cuota_mensual_ars=450000.0,
            ingresos_mensuales_ars=[2000000, 2100000, 1950000],
            valor_credito_usd=25000,
            valor_propiedad_usd=None,
        ),
    }

    for nombre, datos in casos.items():
        resultado = evaluar_legajo(**datos)
        print(nombre, "->", json.dumps(resultado, indent=2, ensure_ascii=False))
        print()
