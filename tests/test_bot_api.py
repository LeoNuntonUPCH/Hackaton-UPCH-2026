"""Pruebas de la API que usará Satqito (bot de Telegram)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app as satq_app
from satq.estado import ESTADO

CLAVE = "bot-prueba"
CABECERA = {"X-Bot-Key": CLAVE}


@pytest.fixture
def cliente(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("SATQ_BOT_API_KEY", CLAVE)
    ESTADO.reiniciar()
    return TestClient(satq_app.app)


def test_sin_clave_configurada(
    cliente: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SATQ_BOT_API_KEY", raising=False)
    respuesta = cliente.get("/api/bot/estado", headers=CABECERA)
    assert respuesta.status_code == 503


def test_clave_incorrecta(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/bot/estado", headers={"X-Bot-Key": "mala"})
    assert respuesta.status_code == 401


def test_estado_para_saludo(cliente: TestClient) -> None:
    respuesta = cliente.get("/api/bot/estado", headers=CABECERA)
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert "nivel_maximo" in datos
    assert "alertas_activas" in datos
    assert "No es una alerta oficial" in datos["aviso"]


def test_quebrada_mas_cercana(cliente: TestClient) -> None:
    respuesta = cliente.get(
        "/api/bot/quebrada", params={"lat": -11.95, "lon": -76.95}, headers=CABECERA
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["codigo"] == "huaycoloro"


def test_suscribir_verificar_y_baja(
    cliente: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("satq.estado.secrets.randbelow", lambda n: 1234)
    respuesta = cliente.post(
        "/api/bot/suscribir",
        headers=CABECERA,
        json={
            "nombre": "Vecina de prueba",
            "telefono": "+51957926893",
            "quebrada": "huaycoloro",
            "chat_id": "123456",
            "usuario": "vecina",
            "consentimiento": True,
        },
    )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["ok"] is True
    assert datos["quebrada"] == "huaycoloro"
    assert datos["verificado"] is False
    assert datos["codigo_enviado"] is True
    assert datos["simulado"] is True

    verificacion = cliente.post(
        "/api/bot/verificar",
        headers=CABECERA,
        json={"telefono": "+51957926893", "codigo": "1234"},
    )
    assert verificacion.status_code == 200
    assert verificacion.json()["ok"] is True

    consulta = cliente.get(
        "/api/bot/suscriptor", params={"chat_id": "123456"}, headers=CABECERA
    )
    assert consulta.status_code == 200
    assert consulta.json()["verificado"] is True
    assert consulta.json()["telefono"] == "+51****6893"

    prueba = cliente.post(
        "/api/bot/probar", headers=CABECERA, json={"chat_id": "123456"}
    )
    assert prueba.status_code == 200
    assert prueba.json()["ok"] is True

    baja = cliente.post(
        "/api/bot/baja",
        headers=CABECERA,
        json={"telefono": "+51957926893"},
    )
    assert baja.status_code == 200
    assert baja.json()["ok"] is True


def test_codigo_incorrecto(
    cliente: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("satq.estado.secrets.randbelow", lambda n: 4321)
    cliente.post(
        "/api/bot/suscribir",
        headers=CABECERA,
        json={
            "telefono": "+51957926893",
            "quebrada": "huaycoloro",
            "chat_id": "999",
            "consentimiento": True,
        },
    )
    respuesta = cliente.post(
        "/api/bot/verificar",
        headers=CABECERA,
        json={"telefono": "+51957926893", "codigo": "0000"},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["ok"] is False
    assert respuesta.json()["intentos"] == 1


def test_suscribir_sin_consentimiento(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/bot/suscribir",
        headers=CABECERA,
        json={
            "telefono": "+51957926893",
            "quebrada": "huaycoloro",
            "chat_id": "1",
            "consentimiento": False,
        },
    )
    assert respuesta.status_code == 400


def test_suscribir_telefono_invalido(cliente: TestClient) -> None:
    respuesta = cliente.post(
        "/api/bot/suscribir",
        headers=CABECERA,
        json={
            "telefono": "123",
            "quebrada": "huaycoloro",
            "chat_id": "1",
            "consentimiento": True,
        },
    )
    assert respuesta.status_code == 400
