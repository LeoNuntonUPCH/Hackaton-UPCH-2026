"""Canal SMS real mediante Infobip (REST, sin dependencias externas)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import ResultadoEnvio

RUTA = "/sms/2/text/advanced"


def _post_json(
    url: str, datos: dict, api_key: str, timeout: int = 10
) -> tuple[int, str]:
    cuerpo = json.dumps(datos).encode("utf-8")
    peticion = urllib.request.Request(
        url,
        data=cuerpo,
        method="POST",
        headers={
            "Authorization": f"App {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
        return respuesta.status, respuesta.read().decode("utf-8")


class CanalInfobip:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        origen: str | None = None,
    ) -> None:
        self.api_key = (api_key or os.environ.get("SATQ_INFOBIP_API_KEY", "")).strip()
        self.base_url = (
            base_url or os.environ.get("SATQ_INFOBIP_BASE_URL", "")
        ).strip().rstrip("/")
        self.origen = (origen or os.environ.get("SATQ_INFOBIP_FROM", "SATQ")).strip()

    def enviar(self, destino: str, texto: str) -> ResultadoEnvio:
        if not (self.api_key and self.base_url):
            return ResultadoEnvio(
                estado="fallido",
                proveedor="infobip",
                error="Faltan credenciales de Infobip (API key o base URL).",
            )
        if not destino or not texto:
            return ResultadoEnvio(
                estado="fallido",
                proveedor="infobip",
                error="Destino o mensaje vacío.",
            )

        datos = {
            "messages": [
                {
                    "from": self.origen,
                    "destinations": [{"to": destino}],
                    "text": texto,
                }
            ]
        }
        try:
            estado_http, cuerpo = _post_json(
                f"{self.base_url}{RUTA}", datos, self.api_key
            )
        except urllib.error.HTTPError as exc:
            detalle = ""
            try:
                detalle = exc.read().decode("utf-8")[:300]
            except Exception:
                detalle = ""
            return ResultadoEnvio(
                estado="fallido",
                proveedor="infobip",
                error=f"Infobip HTTP {exc.code}. {detalle}".strip(),
                intentos=1,
            )
        except Exception as exc:
            return ResultadoEnvio(
                estado="fallido",
                proveedor="infobip",
                error=f"Error de red con Infobip: {exc}",
                intentos=1,
            )

        try:
            respuesta = json.loads(cuerpo or "{}")
        except json.JSONDecodeError:
            respuesta = {}

        mensajes = respuesta.get("messages") or []
        if not mensajes or not isinstance(mensajes[0], dict):
            return ResultadoEnvio(
                estado="fallido",
                proveedor="infobip",
                error="Infobip devolvió una respuesta vacía.",
                intentos=1,
            )

        mensaje = mensajes[0]
        estado_mensaje = mensaje.get("status") or {}
        grupo = estado_mensaje.get("groupId")
        nombre = str(estado_mensaje.get("name", ""))
        if grupo in (1, 3) or nombre in (
            "PENDING_ENROUTE",
            "SENT",
            "DELIVERED",
        ):
            return ResultadoEnvio(
                estado="enviado",
                proveedor="infobip",
                entrega_real="SMS · Infobip",
                id_externo=str(mensaje.get("messageId", "")),
                intentos=1,
            )

        detalle = (
            estado_mensaje.get("description")
            or nombre
            or f"Infobip HTTP {estado_http}."
        )
        return ResultadoEnvio(
            estado="fallido",
            proveedor="infobip",
            error=str(detalle),
            intentos=1,
        )
