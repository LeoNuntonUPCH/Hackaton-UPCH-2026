"""Canales sin red: simulación y proveedor no configurado."""

from __future__ import annotations

from .base import ResultadoEnvio


class CanalSimulado:
    def enviar(self, destino: str, texto: str) -> ResultadoEnvio:
        return ResultadoEnvio(
            estado="pendiente",
            proveedor="simulación",
            entrega_real="No disponible",
        )


class CanalNoConfigurado:
    def __init__(self, motivo: str) -> None:
        self.motivo = motivo

    def enviar(self, destino: str, texto: str) -> ResultadoEnvio:
        return ResultadoEnvio(
            estado="fallido",
            proveedor="no configurado",
            entrega_real="No disponible",
            error=f"Proveedor SMS no configurado ({self.motivo}).",
        )
