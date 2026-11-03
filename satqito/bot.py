"""Satqito: bot de Telegram para suscripción y consulta de alertas."""

from __future__ import annotations

import re
import time
from pathlib import Path

from .api import ApiError, ApiSatq
from .telegram import Telegram, TelegramError

CONSENTIMIENTO = {
    "inline_keyboard": [
        [
            {"text": "Sí, quiero alertas", "callback_data": "consent_si"},
            {"text": "No, gracias", "callback_data": "consent_no"},
        ]
    ]
}

UBICACION = {
    "keyboard": [[{"text": "Compartir mi ubicación", "request_location": True}]],
    "resize_keyboard": True,
    "one_time_keyboard": True,
}

RESPUESTA = {"force_reply": True}


class Satqito:
    def __init__(self, api: ApiSatq, tg: Telegram) -> None:
        self.api = api
        self.tg = tg
        self.estados: dict[int, dict] = {}
        self.offset_file = Path(__file__).resolve().parent.parent / ".satqito_offset"

    def _leer_offset(self) -> int | None:
        try:
            return int(self.offset_file.read_text(encoding="utf-8").strip())
        except Exception:
            return None

    def _guardar_offset(self, offset: int) -> None:
        try:
            self.offset_file.write_text(str(offset), encoding="utf-8")
        except Exception:
            pass

    def run(self) -> None:
        offset = self._leer_offset()
        if offset is None:
            try:
                pendientes = self.tg.get_updates(offset=-1, timeout=0)
                if pendientes:
                    offset = int(pendientes[-1].get("update_id", 0)) + 1
                    self._guardar_offset(offset)
            except TelegramError as exc:
                if "409" in str(exc):
                    print(
                        "Otra instancia de Satqito está usando el mismo token.\n"
                        "Cierra todas las ventanas de Satqito y vuelve a iniciar."
                    )
                    return
        while True:
            try:
                updates = self.tg.get_updates(offset=offset, timeout=30)
            except TelegramError as exc:
                if "409" in str(exc):
                    print(
                        "Otra instancia de Satqito está usando el mismo token.\n"
                        "Cierra todas las ventanas de Satqito y vuelve a iniciar."
                    )
                    return
                print("Error de Telegram:", exc)
                time.sleep(3)
                continue
            for update in updates:
                offset = int(update.get("update_id", 0)) + 1
                self._guardar_offset(offset)
                try:
                    self.manejar(update)
                except Exception as exc:
                    print("Error procesando update:", exc)

    def manejar(self, update: dict) -> None:
        if "message" in update:
            self._mensaje(update["message"])
        elif "callback_query" in update:
            self._callback(update["callback_query"])

    def _estado_chat(self, chat_id: int) -> dict:
        return self.estados.setdefault(chat_id, {"paso": "inicio"})

    # -- mensajes ---------------------------------------------------------

    def _mensaje(self, mensaje: dict) -> None:
        chat = mensaje.get("chat") or {}
        chat_id = chat.get("id")
        if chat_id is None:
            return
        estado = self._estado_chat(chat_id)
        remitente = mensaje.get("from") or {}
        estado["usuario"] = remitente.get("username") or remitente.get("first_name", "")
        estado["nombre"] = remitente.get("first_name", "")

        if mensaje.get("location"):
            if estado.get("paso") == "ubicacion":
                ubicacion = mensaje["location"]
                self._recibir_ubicacion(
                    chat_id,
                    str(estado.get("telefono", "")),
                    float(ubicacion["latitude"]),
                    float(ubicacion["longitude"]),
                    str(estado.get("usuario", "")),
                    str(estado.get("nombre", "")),
                )
            else:
                self.tg.send_message(
                    chat_id, "Para suscribirte, envía /start y elige la opción."
                )
            return

        texto = str(mensaje.get("text", "")).strip()
        if texto.startswith("/start"):
            self._saludo(chat_id)
            return
        if texto.startswith("/ayuda"):
            self._ayuda(chat_id)
            return
        if texto == "/estado":
            self._consultar_estado(chat_id)
            return
        if texto == "/baja":
            self._baja(chat_id)
            return
        if texto == "/probar":
            self._probar(chat_id)
            return
        if estado.get("paso") == "telefono":
            self._recibir_telefono(chat_id, texto, estado)
            return
        if estado.get("paso") == "codigo":
            self._recibir_codigo(chat_id, str(estado.get("telefono", "")), texto)
            return
        if estado.get("paso") == "consentimiento":
            self.tg.send_message(
                chat_id, "Elige una opción con los botones o envía /start."
            )
            return
        if estado.get("paso") == "listo":
            self._ayuda(chat_id)
            return
        self._saludo(chat_id)

    def _ayuda(self, chat_id: int) -> None:
        self.tg.send_message(
            chat_id,
            "Comandos disponibles:\n"
            "/estado · consulta el estado actual\n"
            "/probar · SMS de prueba solo a tu número\n"
            "/baja · cancela tu suscripción\n"
            "/start · volver a empezar",
        )

    def _callback(self, callback: dict) -> None:
        self.tg.answer_callback(str(callback.get("id", "")))
        mensaje = callback.get("message") or {}
        chat_id = (mensaje.get("chat") or {}).get("id")
        if chat_id is None:
            return
        estado = self._estado_chat(chat_id)
        if callback.get("data") == "consent_si":
            estado["paso"] = "telefono"
            self.tg.send_message(
                chat_id,
                "Escribe tu número de celular con código de país.\n"
                "Ejemplo: +51957926893",
                reply_markup=RESPUESTA,
            )
        elif callback.get("data") == "consent_no":
            estado["paso"] = "inicio"
            self.tg.send_message(
                chat_id,
                "Entendido. Puedes consultar el estado cuando quieras con /estado.",
            )

    # -- flujo ------------------------------------------------------------

    def _saludo(self, chat_id: int) -> None:
        try:
            datos = self.api.estado()
        except ApiError as exc:
            self.tg.send_message(chat_id, f"No pude consultar el estado: {exc}")
            return
        nivel = str(datos.get("nivel_maximo", "bajo"))
        if nivel in ("alto", "critico"):
            alerta = f"⚠️ Hay una alerta de nivel {nivel} en el país."
        else:
            alerta = "✅ No hay alertas de riesgo alto activas en este momento."
        texto = (
            "¡Hola! Soy Satqito, el asistente de SATQ Digital. 🏔️\n\n"
            f"{alerta}\n\n"
            "Mi función es avisarte por SMS cuando el riesgo de huaico sea alto "
            "en tu zona. Es una demostración: no es una alerta oficial.\n\n"
            "¿Quieres recibir alertas?"
        )
        self._estado_chat(chat_id)["paso"] = "consentimiento"
        self.tg.send_message(chat_id, texto, reply_markup=CONSENTIMIENTO)

    def _consultar_estado(self, chat_id: int) -> None:
        try:
            datos = self.api.estado()
        except ApiError as exc:
            self.tg.send_message(chat_id, f"No pude consultar el estado: {exc}")
            return
        resumen = datos.get("resumen") or {}
        texto = (
            f"Nivel máximo ahora: {datos.get('nivel_maximo', 'bajo')}.\n"
            f"Alertas activas: {datos.get('alertas_activas', 0)}.\n"
            f"Quebradas monitoreadas: {datos.get('quebradas_monitoreadas', 0)}.\n"
            f"Críticas: {resumen.get('critico', 0)} · Altas: {resumen.get('alto', 0)}.\n\n"
            f"{datos.get('aviso', '')}"
        )
        self.tg.send_message(chat_id, texto)

    def _recibir_telefono(self, chat_id: int, texto: str, estado: dict) -> None:
        digitos = re.sub(r"[^0-9]", "", texto)
        if texto.strip().startswith("+"):
            limpio = "+" + digitos
        elif len(digitos) == 9:
            limpio = "+51" + digitos
        elif len(digitos) == 11 and digitos.startswith("51"):
            limpio = "+" + digitos
        else:
            limpio = "+" + digitos
        if not re.fullmatch(r"\+\d{9,15}", limpio):
            self.tg.send_message(
                chat_id,
                "Ese número no parece válido. Escríbelo con código de país, "
                "por ejemplo +51957926893.",
                reply_markup=RESPUESTA,
            )
            return
        estado["telefono"] = limpio
        estado["paso"] = "ubicacion"
        self.tg.send_message(
            chat_id,
            "Gracias. Ahora comparte tu ubicación para asignarte la quebrada "
            "más cercana.",
            reply_markup=UBICACION,
        )

    def _recibir_ubicacion(
        self,
        chat_id: int,
        telefono: str,
        lat: float,
        lon: float,
        usuario: str,
        nombre: str,
    ) -> None:
        try:
            datos = self.api.suscribir(
                nombre, telefono, "huaycoloro", str(chat_id), usuario, lat, lon
            )
        except ApiError as exc:
            self.tg.send_message(chat_id, f"No pude registrar la suscripción: {exc}")
            return
        estado = self._estado_chat(chat_id)
        estado["paso"] = "codigo"
        estado["quebrada"] = datos.get("quebrada", "")
        if datos.get("codigo_enviado"):
            self.tg.send_message(
                chat_id,
                f"Quedaste asociado a la quebrada {datos.get('quebrada')}.\n"
                f"Enviamos un SMS al {datos.get('telefono')} con un código de "
                "4 dígitos. Escríbelo aquí para verificar tu número.",
                reply_markup=RESPUESTA,
            )
        else:
            error = datos.get("error") or "No se pudo enviar el SMS."
            self.tg.send_message(
                chat_id,
                f"No se pudo enviar el SMS de verificación: {error}\n"
                "Revisa el número o inténtalo más tarde.",
            )

    def _recibir_codigo(self, chat_id: int, telefono: str, codigo: str) -> None:
        if not re.fullmatch(r"\d{4}", codigo.strip()):
            self.tg.send_message(
                chat_id, "El código debe tener 4 dígitos.", reply_markup=RESPUESTA
            )
            return
        try:
            resultado = self.api.verificar(telefono, codigo.strip())
        except ApiError as exc:
            self.tg.send_message(chat_id, f"No pude verificar el código: {exc}")
            return
        if resultado.get("ok"):
            estado = self._estado_chat(chat_id)
            estado["paso"] = "listo"
            self.tg.send_message(
                chat_id,
                f"✅ Listo. Quedaste registrado para la quebrada "
                f"{resultado.get('quebrada')}.\n\n"
                "Recibirás un SMS cuando el riesgo sea alto o crítico.\n"
                "Es una demostración: no es una alerta oficial.\n\n"
                "Comandos: /estado · /probar · /baja · /ayuda",
            )
        else:
            self.tg.send_message(
                chat_id,
                f"{resultado.get('error', 'Código incorrecto.')}\n"
                "Inténtalo de nuevo.",
                reply_markup=RESPUESTA,
            )

    def _baja(self, chat_id: int) -> None:
        try:
            resultado = self.api.baja(str(chat_id))
        except ApiError as exc:
            self.tg.send_message(chat_id, f"No pude procesar la baja: {exc}")
            return
        if resultado.get("ok"):
            self._estado_chat(chat_id)["paso"] = "inicio"
            self.tg.send_message(
                chat_id, "Listo, dimos de baja tu suscripción. No recibirás más SMS."
            )
        else:
            self.tg.send_message(
                chat_id, "No encontré una suscripción activa para este chat."
            )

    def _probar(self, chat_id: int) -> None:
        try:
            resultado = self.api.probar(str(chat_id))
        except ApiError as exc:
            self.tg.send_message(chat_id, f"No pude enviar la prueba: {exc}")
            return
        if resultado.get("ok"):
            self.tg.send_message(
                chat_id,
                "Te envié un SMS de prueba solo a tu número. Revisa tu celular.",
            )
        else:
            error = resultado.get("error") or "No se pudo enviar el SMS de prueba."
            self.tg.send_message(chat_id, f"No se pudo enviar: {error}")
