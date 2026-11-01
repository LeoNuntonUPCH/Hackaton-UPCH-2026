"""Pruebas del estado: transiciones, umbrales, ingesta y alertas."""

from __future__ import annotations

import pytest

from satq.estado import AlertaNoRequerida, ConflictoIngesta, Estado
from satq.motor import Umbrales


def test_escenario_inicial(estado: Estado) -> None:
    assert len(estado.quebradas) == 24
    assert len(estado.alertas) == 7
    assert len(estado.comunicaciones) == 3
    assert len(estado.historial_parametros) == 2
    assert estado.umbrales.ventana_horas == 6


def test_validar_alerta_pendiente(estado: Estado) -> None:
    alerta = estado.alerta("AL-0007")
    assert alerta is not None
    assert alerta.estado == "pendiente"

    estado.validar_alerta("AL-0007", "María Torres")

    assert alerta.estado == "validada"
    assert "Validada por María Torres" in alerta.nota
    assert estado.validar_alerta("NO-EXISTE", "X") is None


def test_cambiar_estado_alerta(estado: Estado) -> None:
    estado.cambiar_estado_alerta("AL-0007", "enviada", "María Torres")
    assert estado.alerta("AL-0007").estado == "enviada"

    estado.cambiar_estado_alerta("AL-0007", "inventado", "María Torres")
    assert estado.alerta("AL-0007").estado == "enviada"


def test_umbrales_invalidos_no_se_guardan(estado: Estado) -> None:
    original = estado.umbrales
    problemas = estado.actualizar_umbrales(
        Umbrales(moderado=30.0, alto=20.0), "Diego Salazar"
    )
    assert problemas
    assert estado.umbrales is original


def test_umbrales_validos_y_recalculo(estado: Estado) -> None:
    historial_antes = len(estado.historial_parametros)
    problemas = estado.actualizar_umbrales(
        Umbrales(critico=50.0), "Diego Salazar"
    )
    assert problemas == []
    assert estado.umbrales.critico == 50.0
    assert len(estado.historial_parametros) > historial_antes

    cambiadas = estado.recalcular_alertas()
    assert cambiadas == 1
    assert estado.alerta("AL-0007").nivel == "alto"


def test_nueva_quebrada_sin_datos(estado: Estado) -> None:
    q = estado.nueva_quebrada("Quebrada Prueba", "Distrito", "Provincia", "Lima")
    assert q.codigo in estado.quebradas
    assert estado.evaluacion(q.codigo).nivel == "sin_datos"


def test_ingesta_idempotente(estado: Estado) -> None:
    r1 = estado.ingerir_lecturas("quirio", [22.0, 18.0], "n8n-demo", "clave-1")
    assert r1["alerta_requerida"] is True
    assert r1["duplicado"] is False
    lecturas = len(estado.quebrada("quirio").lecturas)

    r2 = estado.ingerir_lecturas("quirio", [22.0, 18.0], "n8n-demo", "clave-1")
    assert r2["duplicado"] is True
    assert len(estado.quebrada("quirio").lecturas) == lecturas


def test_ingesta_misma_clave_otro_payload(estado: Estado) -> None:
    estado.ingerir_lecturas("quirio", [10.0], "n8n-demo", "clave-2")
    with pytest.raises(ConflictoIngesta):
        estado.ingerir_lecturas("quirio", [20.0], "n8n-demo", "clave-2")


def test_ingesta_quebrada_inexistente(estado: Estado) -> None:
    with pytest.raises(KeyError):
        estado.ingerir_lecturas("no-existe", [10.0], "n8n-demo", "clave-3")


def test_crear_alerta_si_corresponde(estado: Estado) -> None:
    estado.ingerir_lecturas("quirio", [22.0, 18.0], "n8n-demo", "clave-4")
    creada = estado.crear_alerta_si_corresponde("quirio", "n8n-demo", "clave-4-alerta")
    assert creada["creada"] is True
    assert creada["alerta"]["codigo"] == "AL-0008"

    repetida = estado.crear_alerta_si_corresponde(
        "quirio", "n8n-demo", "clave-4-alerta"
    )
    assert repetida["duplicado"] is True


def test_crear_alerta_nivel_bajo(estado: Estado) -> None:
    with pytest.raises(AlertaNoRequerida):
        estado.crear_alerta_si_corresponde("carosio", "n8n-demo", "clave-5")


def test_no_duplica_alerta_activa(estado: Estado) -> None:
    resultado = estado.crear_alerta_si_corresponde(
        "huaycoloro", "n8n-demo", "clave-6"
    )
    assert resultado["creada"] is False
    assert resultado["motivo"] == "alerta_activa"
