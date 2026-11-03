"""Pruebas del flujo de Satqito sin red ni Telegram real."""

from __future__ import annotations

from satqito.bot import Satqito


class FakeApi:
    def estado(self) -> dict:
        return {
            "nivel_maximo": "alto",
            "alertas_activas": 2,
            "quebradas_monitoreadas": 24,
            "resumen": {"critico": 1, "alto": 1},
            "aviso": "Datos simulados. No es una alerta oficial.",
        }

    def suscribir(self, *args, **kwargs) -> dict:
        return {
            "quebrada": "huaycoloro",
            "telefono": "+51****6893",
            "codigo_enviado": True,
            "error": "",
        }

    def verificar(self, telefono: str, codigo: str) -> dict:
        return {"ok": True, "quebrada": "huaycoloro"}

    def baja(self, chat_id: str) -> dict:
        return {"ok": True}

    def suscriptor(self, chat_id: str) -> dict:
        return {"quebrada": "huaycoloro"}


class FakeTelegram:
    def __init__(self) -> None:
        self.mensajes: list[tuple[int, str]] = []

    def send_message(self, chat_id, texto, reply_markup=None) -> None:
        self.mensajes.append((int(chat_id), str(texto)))

    def answer_callback(self, callback_id: str, texto: str = "") -> None:
        return None


def test_saludo_pide_consentimiento() -> None:
    tg = FakeTelegram()
    bot = Satqito(FakeApi(), tg)  # type: ignore[arg-type]
    bot._saludo(7)
    assert bot.estados[7]["paso"] == "consentimiento"
    assert "alerta de nivel alto" in tg.mensajes[-1][1]
    assert "no es una alerta oficial" in tg.mensajes[-1][1].lower()


def test_consentimiento_si_pide_telefono() -> None:
    tg = FakeTelegram()
    bot = Satqito(FakeApi(), tg)  # type: ignore[arg-type]
    bot._callback(
        {"id": "1", "message": {"chat": {"id": 7}}, "data": "consent_si"}
    )
    assert bot.estados[7]["paso"] == "telefono"
    assert "+51" in tg.mensajes[-1][1]


def test_telefono_invalido_no_avanza() -> None:
    tg = FakeTelegram()
    bot = Satqito(FakeApi(), tg)  # type: ignore[arg-type]
    estado: dict = {"paso": "telefono"}
    bot._recibir_telefono(7, "123", estado)
    assert estado["paso"] == "telefono"


def test_flujo_completo_hasta_verificacion() -> None:
    tg = FakeTelegram()
    bot = Satqito(FakeApi(), tg)  # type: ignore[arg-type]
    estado = bot._estado_chat(7)
    estado["paso"] = "telefono"
    bot._recibir_telefono(7, "+51957926893", estado)
    assert estado["paso"] == "ubicacion"
    assert estado["telefono"] == "+51957926893"

    bot._recibir_ubicacion(7, estado["telefono"], -11.95, -76.95, "vecina", "Ana")
    assert bot.estados[7]["paso"] == "codigo"

    bot._recibir_codigo(7, estado["telefono"], "1234")
    assert bot.estados[7]["paso"] == "listo"


def test_baja_responde() -> None:
    tg = FakeTelegram()
    bot = Satqito(FakeApi(), tg)  # type: ignore[arg-type]
    bot._baja(7)
    assert "dimos de baja" in tg.mensajes[-1][1]
