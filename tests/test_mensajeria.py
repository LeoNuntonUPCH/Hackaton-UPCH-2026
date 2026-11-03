"""Pruebas de mensajería: canales, topes e idempotencia (sin red)."""

from __future__ import annotations

import json

import pytest

from mensajeria import ResultadoEnvio, obtener_canal
from mensajeria.simulado import CanalSimulado
from mensajeria.sms_infobip import CanalInfobip
from mensajeria.sms_twilio import CanalTwilio
from mensajeria.sms_vonage import CanalVonage
from satq.estado import Estado


class CanalFalso:
    def __init__(self, estado: str = "enviado") -> None:
        self.estado = estado
        self.llamadas: list[tuple[str, str]] = []

    def enviar(self, destino: str, texto: str) -> ResultadoEnvio:
        self.llamadas.append((destino, texto))
        return ResultadoEnvio(
            estado=self.estado,
            proveedor="falso",
            entrega_real="SMS · Falso",
        )


def test_simulado_no_envia() -> None:
    resultado = CanalSimulado().enviar("+51999888777", "Hola")
    assert resultado.estado == "pendiente"
    assert resultado.proveedor == "simulación"


def test_fabrica_usa_simulado_sin_modo_real(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SATQ_SMS_MODO", "simulado")
    assert isinstance(obtener_canal("SMS"), CanalSimulado)


def test_whatsapp_siempre_simulado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SATQ_SMS_MODO", "real")
    monkeypatch.setenv("SATQ_SMS_PROVEEDOR", "twilio")
    assert isinstance(obtener_canal("WhatsApp"), CanalSimulado)


def test_twilio_sin_credenciales(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SATQ_TWILIO_SID", raising=False)
    monkeypatch.delenv("SATQ_TWILIO_TOKEN", raising=False)
    monkeypatch.delenv("SATQ_TWILIO_FROM", raising=False)
    resultado = CanalTwilio(sid="", token="", origen="").enviar("+51999888777", "Hola")
    assert resultado.estado == "fallido"
    assert "credenciales" in resultado.error.lower()


def test_twilio_envio_correcto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mensajeria.sms_twilio._post_form",
        lambda *a, **k: (201, json.dumps({"sid": "SM123", "status": "queued"})),
    )
    resultado = CanalTwilio(sid="AC1", token="token", origen="+1555").enviar(
        "+51999888777", "Hola"
    )
    assert resultado.estado == "enviado"
    assert resultado.id_externo == "SM123"
    assert resultado.proveedor == "twilio"


def test_twilio_error_de_red(monkeypatch: pytest.MonkeyPatch) -> None:
    def falla(*a, **k):
        raise OSError("sin red")

    monkeypatch.setattr("mensajeria.sms_twilio._post_form", falla)
    resultado = CanalTwilio(sid="AC1", token="token", origen="+1555").enviar(
        "+51999888777", "Hola"
    )
    assert resultado.estado == "fallido"
    assert "red" in resultado.error.lower()


def test_vonage_envio_correcto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mensajeria.sms_vonage._post_form",
        lambda *a, **k: (
            200,
            json.dumps({"messages": [{"status": "0", "message-id": "V1"}]}),
        ),
    )
    resultado = CanalVonage(api_key="k", api_secret="s", origen="SATQ").enviar(
        "+51999888777", "Hola"
    )
    assert resultado.estado == "enviado"
    assert resultado.id_externo == "V1"


def test_vonage_rechazo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mensajeria.sms_vonage._post_form",
        lambda *a, **k: (
            200,
            json.dumps({"messages": [{"status": "4", "error-text": "rechazado"}]}),
        ),
    )
    resultado = CanalVonage(api_key="k", api_secret="s", origen="SATQ").enviar(
        "+51999888777", "Hola"
    )
    assert resultado.estado == "fallido"
    assert "rechazado" in resultado.error


def test_infobip_envio_correcto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mensajeria.sms_infobip._post_json",
        lambda *a, **k: (
            200,
            json.dumps(
                {
                    "messages": [
                        {
                            "messageId": "IB1",
                            "status": {"groupId": 1, "name": "PENDING_ENROUTE"},
                        }
                    ]
                }
            ),
        ),
    )
    resultado = CanalInfobip(
        api_key="k", base_url="https://demo.api.infobip.com", origen="SATQ"
    ).enviar("+51999888777", "Hola")
    assert resultado.estado == "enviado"
    assert resultado.id_externo == "IB1"
    assert resultado.proveedor == "infobip"


def test_infobip_rechazo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "mensajeria.sms_infobip._post_json",
        lambda *a, **k: (
            200,
            json.dumps(
                {
                    "messages": [
                        {
                            "messageId": "IB2",
                            "status": {
                                "groupId": 5,
                                "name": "REJECTED",
                                "description": "Rejected",
                            },
                        }
                    ]
                }
            ),
        ),
    )
    resultado = CanalInfobip(
        api_key="k", base_url="https://demo.api.infobip.com", origen="SATQ"
    ).enviar("+51999888777", "Hola")
    assert resultado.estado == "fallido"
    assert "Rejected" in resultado.error


def test_infobip_sin_credenciales(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SATQ_INFOBIP_API_KEY", raising=False)
    monkeypatch.delenv("SATQ_INFOBIP_BASE_URL", raising=False)
    resultado = CanalInfobip(api_key="", base_url="").enviar("+51999888777", "Hola")
    assert resultado.estado == "fallido"
    assert "credenciales" in resultado.error.lower()


def test_fabrica_infobip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SATQ_SMS_MODO", "real")
    monkeypatch.setenv("SATQ_SMS_PROVEEDOR", "infobip")
    assert isinstance(obtener_canal("SMS"), CanalInfobip)


def test_registrar_comunicacion_simulada(estado: Estado) -> None:
    nuevas = estado.registrar_comunicacion(
        "huaycoloro", 12, ["SMS", "WhatsApp"], texto="Hola", plantilla="preventivo"
    )
    assert [c.resultado for c in nuevas] == ["pendiente", "pendiente"]
    assert nuevas[0].proveedor == "simulación"


def test_registrar_sms_real_con_tope_e_idempotencia(
    estado: Estado, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SATQ_SMS_MODO", "real")
    monkeypatch.setenv("SATQ_SMS_DESTINO", "+51999888777")
    monkeypatch.setenv("SATQ_SMS_MAX_ENVIOS", "5")
    falso = CanalFalso()
    monkeypatch.setattr("satq.estado.obtener_canal", lambda nombre="SMS": falso)

    primera = estado.registrar_comunicacion(
        "huaycoloro", 12, ["SMS"], texto="Alerta", plantilla="preventivo"
    )
    assert primera[0].resultado == "enviado"
    assert primera[0].destino == "+51****8777"
    assert falso.llamadas == [("+51999888777", "Alerta")]

    segunda = estado.registrar_comunicacion(
        "huaycoloro", 12, ["SMS"], texto="Alerta", plantilla="preventivo"
    )
    assert segunda[0].resultado == "pendiente"
    assert len(falso.llamadas) == 1


def test_registrar_sms_sin_destino(
    estado: Estado, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SATQ_SMS_MODO", "real")
    monkeypatch.delenv("SATQ_SMS_DESTINO", raising=False)
    nuevas = estado.registrar_comunicacion(
        "huaycoloro", 12, ["SMS"], texto="Alerta", plantilla="preventivo"
    )
    assert nuevas[0].resultado == "fallido"
    assert "destino" in nuevas[0].error.lower()
