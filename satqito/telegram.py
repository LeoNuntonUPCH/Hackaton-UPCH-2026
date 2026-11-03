"""Cliente mínimo de la Bot API de Telegram (solo librería estándar)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request


class TelegramError(Exception):
    """Error al llamar a la Bot API."""


class Telegram:
    def __init__(self, token: str) -> None:
        self.token = token

    def _llamar(self, metodo: str, **params) -> object:
        url = f"https://api.telegram.org/bot{self.token}/{metodo}"
        peticion = urllib.request.Request(
            url,
            data=json.dumps(params).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(peticion, timeout=60) as respuesta:
                datos = json.loads(respuesta.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detalle = ""
            try:
                detalle = exc.read().decode("utf-8")[:200]
            except Exception:
                detalle = ""
            raise TelegramError(
                f"Telegram HTTP {exc.code}: {detalle}".strip()
            ) from exc
        except Exception as exc:
            raise TelegramError(f"Error de red con Telegram: {exc}") from exc
        if not datos.get("ok"):
            raise TelegramError(str(datos.get("description", "Error de Telegram")))
        return datos.get("result")

    def get_updates(self, offset: int | None = None, timeout: int = 30) -> list:
        params: dict = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        resultado = self._llamar("getUpdates", **params)
        return resultado if isinstance(resultado, list) else []

    def send_message(
        self,
        chat_id: int | str,
        texto: str,
        reply_markup: dict | None = None,
    ) -> object:
        params: dict = {"chat_id": chat_id, "text": texto}
        if reply_markup is not None:
            params["reply_markup"] = reply_markup
        return self._llamar("sendMessage", **params)

    def answer_callback(self, callback_id: str, texto: str = "") -> object:
        return self._llamar(
            "answerCallbackQuery", callback_query_id=callback_id, text=texto
        )
