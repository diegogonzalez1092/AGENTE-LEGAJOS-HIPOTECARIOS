"""
Herramientas deterministas del agente de análisis financiero de legajos hipotecarios.

Estas funciones NO usan el LLM: son cálculos aritméticos verificables, expuestos
al modelo como tool calls (ver agente/legajo_agent.py) para que la decisión de
aprobación nunca dependa de que Claude "haga la cuenta bien" en texto libre.
Esta separación (LLM extrae y redacta, código calcula) es una decisión de
gobierno documentada en DECISIONES.md y GOBIERNO_Y_RIESGO.md.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional

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
    cuota_mensual_ars: float,
    ingreso_neto_mensual_ars: float,
    valor_credito_usd: float,
    valor_propiedad_usd: float,
) -> dict:
    """Aplica los dos controles duros y arma la decisión final + motivo si corresponde.

    Esta es la función expuesta como tool al modelo (ver agente/legajo_agent.py).
    """
    control_1 = evaluar_control_cuota_ingreso(cuota_mensual_ars, ingreso_neto_mensual_ars)
    control_2 = evaluar_control_ltv(valor_credito_usd, valor_propiedad_usd)

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
        "control_1_cuota_ingreso": control_1.to_dict(),
        "control_2_ltv": control_2.to_dict(),
        "resultado_final": "ok credito aprobado" if aprobado else "credito no aprobado",
        "motivo": None if aprobado else "; ".join(motivos),
    }


if __name__ == "__main__":
    import json

    # Los tres legajos reales de la carpeta de Drive "Trabajo Final - Creación
    # agentes de IA", con los datos ya extraídos del "Resumen Carpeta" de cada uno.
    # Ver corridas/ para el detalle de extracción por legajo.
    casos = {
        "Perez": dict(
            cuota_mensual_ars=739378.83,
            ingreso_neto_mensual_ars=(2587123 + 2809243 + 2726198) / 3,
            valor_credito_usd=20000,
            valor_propiedad_usd=98000,
        ),
        "Gonzalez": dict(
            cuota_mensual_ars=1066974.90,
            ingreso_neto_mensual_ars=(2758900 + 2150300 + 2945600 + 3029535 + 2635650 + 2739680) / 6,
            valor_credito_usd=33000,
            valor_propiedad_usd=120000,
        ),
        "Lopez": dict(
            cuota_mensual_ars=735475.99,
            ingreso_neto_mensual_ars=(282505 + 70000 + 379192 + 1741680 + 1741680 + 6000000) / 6,
            valor_credito_usd=21452,
            valor_propiedad_usd=53000,
        ),
    }

    for nombre, datos in casos.items():
        resultado = evaluar_legajo(**datos)
        print(nombre, "-> ingreso promedio:", round(datos["ingreso_neto_mensual_ars"], 2))
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        print()
