"""Pruebas de observabilidad: salud y métricas."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import app as satq_app
from satq import observabilidad


@pytest.fixture(autouse=True)
def _metricas_limpias() -> None:
    observabilidad.reiniciar_metricas()
    yield
    observabilidad.reiniciar_metricas()


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(satq_app.app)


def test_health_en_memoria(cliente: TestClient) -> None:
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["estado"] == "ok"
    assert datos["base_datos"]["modo"] == "memoria"
    assert datos["base_datos"]["conectada"] is None


def test_metricas_cuentan_peticiones(cliente: TestClient) -> None:
    cliente.get("/health")
    cliente.get("/login")

    datos = cliente.get("/api/metricas").json()

    assert datos["peticiones_total"] >= 2
    assert any("/health" in ruta for ruta in datos["peticiones_por_ruta"])
    assert datos["duracion_max_ms"] >= 0
    assert datos["ultima_peticion"] is not None


def test_registrar_peticion_directa() -> None:
    observabilidad.registrar_peticion("POST", "/api/ingesta", 201, 12.5)
    datos = observabilidad.resumen_metricas()
    assert datos["peticiones_total"] == 1
    assert datos["errores_5xx"] == 0
    assert datos["peticiones_por_ruta"]["POST /api/ingesta"] == 1
    assert datos["ultima_peticion"]["estado"] == 201

    observabilidad.registrar_peticion("GET", "/roto", 500, 3.0)
    datos = observabilidad.resumen_metricas()
    assert datos["errores_5xx"] == 1
    assert datos["duracion_promedio_ms"] > 0


def test_salud_degradada_si_falla_la_base(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        observabilidad,
        "estado_base_datos",
        lambda: {"modo": "postgres", "conectada": False, "error": "sin conexión"},
    )
    salud = observabilidad.estado_salud()
    assert salud["estado"] == "degradado"
    assert salud["base_datos"]["conectada"] is False


def test_health_degradado_devuelve_503(
    cliente: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        observabilidad,
        "estado_base_datos",
        lambda: {"modo": "postgres", "conectada": False, "error": "sin conexión"},
    )
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 503
    assert respuesta.json()["estado"] == "degradado"


def test_configurar_logs_es_idempotente() -> None:
    import logging

    registro = logging.getLogger("satq")
    observabilidad.configurar_logs()
    handlers = len(registro.handlers)
    observabilidad.configurar_logs()
    assert len(registro.handlers) == handlers
