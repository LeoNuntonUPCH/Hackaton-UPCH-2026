"""Cliente HTTP de Satqito hacia la API de SATQ Digital."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request


class ApiError(Exception):
    """Error al comunicarse con la API de SATQ."""


class ApiSatq:
    def __init__(self, base_url: str, clave: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.clave = clave

    def _request(
        self,
        metodo: str,
        ruta: str,
        params: dict | None = None,
        datos: dict | None = None,
    ) -> dict:
        url = self.base_url + ruta
        if params:
            url += "?" + urllib.parse.urlencode(params)
        cuerpo = json.dumps(datos).encode("utf-8") if datos is not None else None
        peticion = urllib.request.Request(
            url,
            data=cuerpo,
            method=metodo,
            headers={
                "X-Bot-Key": self.clave,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(peticion, timeout=15) as respuesta:
                return json.loads(respuesta.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detalle = ""
            try:
                detalle = exc.read().decode("utf-8")[:200]
            except Exception:
                detalle = ""
            raise ApiError(f"SATQ respondió {exc.code}. {detalle}".strip()) from exc
        except Exception as exc:
            raise ApiError(f"No se pudo conectar con SATQ: {exc}") from exc

    def estado(self) -> dict:
        return self._request("GET", "/api/bot/estado")

    def quebrada(self, lat: float, lon: float) -> dict:
        return self._request(
            "GET", "/api/bot/quebrada", params={"lat": lat, "lon": lon}
        )

    def suscribir(
        self,
        nombre: str,
        telefono: str,
        quebrada: str,
        chat_id: str,
        usuario: str,
        lat: float | None = None,
        lon: float | None = None,
    ) -> dict:
        datos = {
            "nombre": nombre,
            "telefono": telefono,
            "quebrada": quebrada,
            "chat_id": chat_id,
            "usuario": usuario,
            "consentimiento": True,
        }
        if lat is not None and lon is not None:
            datos["lat"] = lat
            datos["lon"] = lon
        return self._request("POST", "/api/bot/suscribir", datos=datos)

    def verificar(self, telefono: str, codigo: str) -> dict:
        return self._request(
            "POST",
            "/api/bot/verificar",
            datos={"telefono": telefono, "codigo": codigo},
        )

    def baja(self, chat_id: str) -> dict:
        return self._request("POST", "/api/bot/baja", datos={"chat_id": chat_id})

    def probar(self, chat_id: str) -> dict:
        return self._request("POST", "/api/bot/probar", datos={"chat_id": chat_id})

    def suscriptor(self, chat_id: str) -> dict:
        return self._request(
            "GET", "/api/bot/suscriptor", params={"chat_id": chat_id}
        )
