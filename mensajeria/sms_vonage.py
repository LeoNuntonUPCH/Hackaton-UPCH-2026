"""Canal SMS real mediante Vonage (REST, sin dependencias externas)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from .base import ResultadoEnvio

URL = "https://rest.nexmo.com/sms/json"


def _post_form(url: str, datos: dict[str, str], timeout: int = 10) -> tuple[int, str]:
    cuerpo = urllib.parse.urlencode(datos).encode("utf-8")
    peticion = urllib.request.Request(
        url,
        data=cuerpo,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
        return respuesta.status, respuesta.read().decode("utf-8")


class CanalVonage:
    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        origen: str | None = None,
    ) -> None:
        self.api_key = (api_key or os.environ.get("SATQ_VONAGE_API_KEY", "")).strip()
        self.api_secret = (
            api_secret or os.environ.get("SATQ_VONAGE_API_SECRET", "")
        ).strip()
        self.origen = (origen or os.environ.get("SATQ_VONAGE_FROM", "SATQ")).strip()

    def enviar(self, destino: str, texto: str) -> ResultadoEnvio:
        if not (self.api_key and self.api_secret):
            return ResultadoEnvio(
                estado="fallido",
                proveedor="vonage",
                error="Faltan credenciales de Vonage.",
            )
        if not destino or not texto:
            return ResultadoEnvio(
                estado="fallido",
                proveedor="vonage",
                error="Destino o mensaje vacío.",
            )
        try:
            estado_http, cuerpo = _post_form(
                URL,
                {
                    "api_key": self.api_key,
                    "api_secret": self.api_secret,
                    "from": self.origen,
                    "to": destino,
                    "text": texto,
                },
            )
        except urllib.error.HTTPError as exc:
            return ResultadoEnvio(
                estado="fallido",
                proveedor="vonage",
                error=f"Vonage HTTP {exc.code}.",
                intentos=1,
            )
        except Exception as exc:
            return ResultadoEnvio(
                estado="fallido",
                proveedor="vonage",
                error=f"Error de red con Vonage: {exc}",
                intentos=1,
            )

        try:
            datos = json.loads(cuerpo or "{}")
        except json.JSONDecodeError:
            datos = {}

        mensajes = datos.get("messages") or [{}]
        mensaje = mensajes[0] if isinstance(mensajes[0], dict) else {}
        if str(mensaje.get("status")) == "0":
            return ResultadoEnvio(
                estado="enviado",
                proveedor="vonage",
                entrega_real="SMS · Vonage",
                id_externo=str(mensaje.get("message-id", "")),
                intentos=1,
            )
        return ResultadoEnvio(
            estado="fallido",
            proveedor="vonage",
            error=str(mensaje.get("error-text") or "Vonage rechazó el mensaje."),
            intentos=1,
        )
