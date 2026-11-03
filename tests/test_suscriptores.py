"""Pruebas de suscriptores, cercanía y despacho de alertas."""

from __future__ import annotations

import pytest

from mensajeria import ResultadoEnvio
from satq.estado import Estado


class CanalFalso:
    def __init__(self) -> None:
        self.llamadas: list[tuple[str, str]] = []

    def enviar(self, destino: str, texto: str) -> ResultadoEnvio:
        self.llamadas.append((destino, texto))
        return ResultadoEnvio(
            estado="enviado", proveedor="falso", entrega_real="SMS · Falso"
        )


def test_suscribir_valido(estado: Estado) -> None:
    s = estado.suscribir(
        "Vecino", "+51999888777", "huaycoloro", consentimiento=True
    )
    assert s.telefono == "+51999888777"
    assert s.quebrada == "huaycoloro"
    assert s.activo is True
    assert s in estado.suscriptores


def test_suscribir_sin_consentimiento(estado: Estado) -> None:
    with pytest.raises(ValueError):
        estado.suscribir("Vecino", "+51999888777", "huaycoloro", False)


def test_suscribir_telefono_invalido(estado: Estado) -> None:
    with pytest.raises(ValueError):
        estado.suscribir("Vecino", "123", "huaycoloro", True)


def test_suscribir_quebrada_inexistente(estado: Estado) -> None:
    with pytest.raises(KeyError):
        estado.suscribir("Vecino", "+51999888777", "no-existe", True)


def test_ubicacion_asigna_quebrada_mas_cercana(estado: Estado) -> None:
    s = estado.suscribir(
        "Vecino", "+51999888777", "quirio", True, lat=-11.95, lon=-76.95
    )
    assert s.quebrada == "huaycoloro"


def test_baja_suscriptor(estado: Estado) -> None:
    estado.suscribir("Vecino", "+51999888777", "huaycoloro", True)
    assert estado.baja_suscriptor("+51999888777") is True
    activos = estado.suscriptores_activos("huaycoloro")
    assert activos == []
    assert estado.baja_suscriptor("+51999999999") is False


def test_despacho_simulado(estado: Estado) -> None:
    estado.suscribir("Uno", "+51999888777", "huaycoloro", True)
    estado.suscribir("Dos", "+51999777666", "huaycoloro", True)
    estado.suscribir("Tres", "+51999666555", "quirio", True)

    nuevas = estado.despachar_alerta("huaycoloro", "Alerta de prueba", "preventivo")

    assert len(nuevas) == 2
    assert all(c.resultado == "pendiente" for c in nuevas)
    assert all(c.proveedor == "simulación" for c in nuevas)
    assert all(c.canal == "SMS" for c in nuevas)


def test_despacho_real_con_allowlist_y_idempotencia(
    estado: Estado, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SATQ_SMS_MODO", "real")
    monkeypatch.setenv("SATQ_SMS_DESTINOS_PERMITIDOS", "+51999888777")
    monkeypatch.setenv("SATQ_SMS_MAX_ENVIOS", "5")
    falso = CanalFalso()
    monkeypatch.setattr("satq.estado.obtener_canal", lambda nombre="SMS": falso)

    estado.suscribir("Uno", "+51999888777", "huaycoloro", True)
    primera = estado.despachar_alerta("huaycoloro", "Alerta", "preventivo")
    assert primera[0].resultado == "enviado"
    assert primera[0].destino == "+51****8777"
    assert falso.llamadas == [("+51999888777", "Alerta")]

    segunda = estado.despachar_alerta("huaycoloro", "Alerta", "preventivo")
    assert segunda[0].resultado == "pendiente"
    assert len(falso.llamadas) == 1


def test_despacho_destino_no_permitido(
    estado: Estado, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SATQ_SMS_MODO", "real")
    monkeypatch.setenv("SATQ_SMS_DESTINOS_PERMITIDOS", "+51999000000")
    monkeypatch.setattr(
        "satq.estado.obtener_canal", lambda nombre="SMS": CanalFalso()
    )
    estado.suscribir("Uno", "+51999888777", "huaycoloro", True)

    nuevas = estado.despachar_alerta("huaycoloro", "Alerta", "preventivo")
    assert nuevas[0].resultado == "fallido"
    assert "no permitido" in nuevas[0].error.lower()


def test_alerta_auto_despacha_a_suscriptores(
    estado: Estado, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SATQ_ALERTAS_AUTO", "1")
    estado.suscribir("Uno", "+51999888777", "quirio", True)
    estado.ingerir_lecturas("quirio", [22.0, 18.0], "n8n-demo", "auto-1")

    resultado = estado.crear_alerta_si_corresponde(
        "quirio", "n8n-demo", "auto-1-alerta"
    )

    assert resultado["creada"] is True
    auto = [
        c
        for c in estado.comunicaciones
        if c.quebrada == "quirio"
        and c.clave_idempotencia.startswith("quirio:sms:preventivo")
    ]
    assert len(auto) == 1
    assert auto[0].resultado == "pendiente"


def test_resuscribir_mismo_chat_desactiva_anterior(estado: Estado) -> None:
    primero = estado.suscribir_telegram(
        "Ana", "+51957926893", "huaycoloro", "chat-1"
    )
    segundo = estado.suscribir_telegram(
        "Ana", "+51911112222", "quirio", "chat-1"
    )

    assert primero.activo is False
    assert segundo.activo is True
    activo = estado.suscriptor_por_chat("chat-1")
    assert activo is not None
    assert activo.telefono == "+51911112222"


def test_limite_de_codigo_por_minuto(estado: Estado) -> None:
    estado.suscribir_telegram("Ana", "+51957926893", "huaycoloro", "chat-2")
    primero = estado.iniciar_verificacion("+51957926893")
    segundo = estado.iniciar_verificacion("+51957926893")

    assert primero["enviado"] is True
    assert segundo["enviado"] is False
    assert "60 segundos" in segundo["error"]


def test_modo_abierto_permite_cualquier_numero(
    estado: Estado, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SATQ_SMS_MODO", "real")
    monkeypatch.setenv("SATQ_SMS_PERMITIR_ABIERTOS", "1")
    monkeypatch.setenv("SATQ_SMS_MAX_ENVIOS", "5")
    falso = CanalFalso()
    monkeypatch.setattr("satq.estado.obtener_canal", lambda nombre="SMS": falso)

    estado.suscribir("Ana", "+51911112222", "huaycoloro", True)
    nuevas = estado.despachar_alerta("huaycoloro", "Alerta", "preventivo")

    assert nuevas[0].resultado == "enviado"
    assert falso.llamadas[0][0] == "+51911112222"


def test_telefono_de_9_digitos_asume_peru(estado: Estado) -> None:
    suscriptor = estado.suscribir("Ana", "957926893", "huaycoloro", True)
    assert suscriptor.telefono == "+51957926893"


def test_verificacion_queda_en_historial(estado: Estado) -> None:
    estado.suscribir_telegram("Ana", "957926893", "huaycoloro", "chat-3")
    estado.iniciar_verificacion("957926893")
    assert any(
        c.clave_idempotencia.startswith("verificacion:")
        for c in estado.comunicaciones
    )


def test_validar_alerta_alta_envia_sms(
    estado: Estado, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SATQ_ALERTAS_AUTO", "1")
    estado.suscribir("Ana", "+51957926893", "huaycoloro", True)

    estado.validar_alerta("AL-0007", "Autoridad")

    avisos = [
        c
        for c in estado.comunicaciones
        if c.quebrada == "huaycoloro" and c.clave_idempotencia.startswith("huaycoloro:sms")
    ]
    assert len(avisos) == 1
    assert avisos[0].resultado == "pendiente"


def test_accion_notificar_alerta(estado: Estado) -> None:
    from satq import vistas

    estado.suscribir("Ana", "+51957926893", "huaycoloro", True)
    destino = vistas.accion_notificar_alerta(estado, {"alerta": "AL-0007"})

    assert destino.startswith("/alertas?alerta=AL-0007")
    avisos = [
        c for c in estado.comunicaciones if c.clave_idempotencia.startswith("huaycoloro:sms")
    ]
    assert len(avisos) == 1


def test_suscriptor_sin_verificar_no_recibe_alertas(estado: Estado) -> None:
    estado.suscribir_telegram("Ana", "+51957926893", "huaycoloro", "chat-x")
    nuevas = estado.despachar_alerta("huaycoloro", "Alerta", "preventivo")
    assert nuevas == []
