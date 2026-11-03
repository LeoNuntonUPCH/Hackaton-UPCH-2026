"""Canales de mensajería de SATQ Digital."""

from .base import (
    Canal,
    ResultadoEnvio,
    maximo_envios,
    modo_real,
    obtener_canal,
    proveedor_configurado,
)
from .simulado import CanalNoConfigurado, CanalSimulado

__all__ = [
    "Canal",
    "ResultadoEnvio",
    "CanalSimulado",
    "CanalNoConfigurado",
    "modo_real",
    "proveedor_configurado",
    "maximo_envios",
    "obtener_canal",
]
