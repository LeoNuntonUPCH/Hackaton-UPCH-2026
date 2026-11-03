"""Canal SMS real mediante Twilio (REST, sin dependencias externas)."""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request

from .base import ResultadoEnvio

URL = "https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"


def _post_form(
    url: str, datos: dict[str, str], usuario: str, clave: str, timeout: int = 10
) -> tuple[int, str]:
    cuerpo = urllib.parse.urlencode(datos).encode("utf-8")
    credencial = base64.b64encode(f"{usuario}:{clave}".encode("utf-8")).decode("ascii")
    peticion = urllib.request.Request(
        url,
        data=cuerpo,
        method="POST",
        headers={
            "Authorization": f"Basic {credencial}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
        return respuesta.status, respuesta.read().decode("utf-8")


class CanalTwilio:
    def __init__(
        self,
        sid: str | None = None,
        token: str | None = None,
        origen: str | None = None,
    ) -> None:
        self.sid = (sid or os.environ.get("SATQ_TWILIO_SID", "")).strip()
        self.token = (token or os.environ.get("SATQ_TWILIO_TOKEN", "")).strip()
        self.origen = (origen or os.environ.get("SATQ_TWILIO_FROM", "")).strip()

    def enviar(self, destino: str, texto: str) -> ResultadoEnvio:
        if not (self.sid and self.token and self.origen):
            return ResultadoEnvio(
                estado="fallido",
                proveedor="twilio",
                error="Faltan credenciales de Twilio.",
            )
        if not destino or not texto:
            return ResultadoEnvio(
                estado="fallido",
                proveedor="twilio",
                error="Destino o mensaje vacío.",
            )
        try:
            estado_http, cuerpo = _post_form(
                URL.format(sid=self.sid),
                {"From": self.origen, "To": destino, "Body": texto},
                self.sid,
                self.token,
            )
        except urllib.error.HTTPError as exc:
            detalle = ""
            try:
                detalle = exc.read().decode("utf-8")[:200]
            except Exception:
                detalle = ""
            return ResultadoEnvio(
                estado="fallido",
                proveedor="twilio",
                error=f"Twilio HTTP {exc.code}. {detalle}".strip(),
                intentos=1,
            )
        except Exception as exc:
            return ResultadoEnvio(
                estado="fallido",
                proveedor="twilio",
                error=f"Error de red con Twilio: {exc}",
                intentos=1,
            )

        try:
            datos = json.loads(cuerpo or "{}")
        except json.JSONDecodeError:
            datos = {}

        if estado_http >= 400:
            return ResultadoEnvio(
                estado="fallido",
                proveedor="twilio",
                error=f"Twilio HTTP {estado_http}.",
                intentos=1,
            )
        return ResultadoEnvio(
            estado="enviado",
            proveedor="twilio",
            entrega_real="SMS · Twilio",
            id_externo=str(datos.get("sid", "")),
            intentos=1,
        )
