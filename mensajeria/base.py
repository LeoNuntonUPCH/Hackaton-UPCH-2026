"""Contrato común de canales de mensajería."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


@dataclass
class ResultadoEnvio:
    """Resultado normalizado de cualquier canal."""

    estado: str  # enviado | fallido | pendiente
    proveedor: str
    entrega_real: str = "No disponible"
    id_externo: str = ""
    error: str = ""
    intentos: int = 0


class Canal(Protocol):
    def enviar(self, destino: str, texto: str) -> ResultadoEnvio: ...


def modo_real() -> bool:
    return os.environ.get("SATQ_SMS_MODO", "simulado").strip().lower() == "real"


def proveedor_configurado() -> str:
    return os.environ.get("SATQ_SMS_PROVEEDOR", "").strip().lower()


def maximo_envios() -> int:
    try:
        return max(0, int(os.environ.get("SATQ_SMS_MAX_ENVIOS", "10") or "10"))
    except ValueError:
        return 10


def obtener_canal(nombre: str = "SMS") -> Canal:
    """Devuelve el canal adecuado según el entorno.

    WhatsApp y cualquier canal distinto de SMS se mantienen simulados.
    """
    if nombre.strip().lower() != "sms" or not modo_real():
        from .simulado import CanalSimulado

        return CanalSimulado()

    proveedor = proveedor_configurado()
    if proveedor == "twilio":
        from .sms_twilio import CanalTwilio

        return CanalTwilio()
    if proveedor == "vonage":
        from .sms_vonage import CanalVonage

        return CanalVonage()
    if proveedor == "infobip":
        from .sms_infobip import CanalInfobip

        return CanalInfobip()

    from .simulado import CanalNoConfigurado

    return CanalNoConfigurado(proveedor or "sin proveedor")
