"""Pruebas del motor de umbrales: la regla única del sistema."""

from __future__ import annotations

import pytest

from satq.motor import (
    Umbrales,
    acumulado_movil,
    clasificar,
    evaluar,
    resumen_por_nivel,
)


@pytest.mark.parametrize(
    ("acumulado", "esperado"),
    [
        (None, "sin_datos"),
        (0.0, "bajo"),
        (19.9, "bajo"),
        (20.0, "moderado"),
        (29.9, "moderado"),
        (30.0, "alto"),
        (39.9, "alto"),
        (40.0, "critico"),
        (500.0, "critico"),
    ],
)
def test_clasificar_por_limites(acumulado: float | None, esperado: str) -> None:
    assert clasificar(acumulado, Umbrales()) == esperado


def test_sin_lectura_no_es_bajo() -> None:
    assert clasificar(None, Umbrales()) == "sin_datos"


@pytest.mark.parametrize(
    ("lecturas", "ventana", "esperado"),
    [
        ([1.0, 2.0, 3.0, 4.0], 3, [1.0, 3.0, 6.0, 9.0]),
        ([1.0, 2.0, 3.0, 4.0], 1, [1.0, 2.0, 3.0, 4.0]),
        ([1.0, 2.0, 3.0, 4.0], 6, [1.0, 3.0, 6.0, 10.0]),
        ([], 6, []),
    ],
)
def test_acumulado_movil(
    lecturas: list[float], ventana: int, esperado: list[float]
) -> None:
    assert acumulado_movil(lecturas, ventana) == esperado


def test_umbrales_por_defecto_son_validos() -> None:
    assert Umbrales().validar() == []


def test_umbrales_bajo_distinto_de_cero() -> None:
    problemas = Umbrales(bajo=1.0).validar()
    assert any("debe ser 0" in p for p in problemas)


def test_umbrales_no_crecientes() -> None:
    problemas = Umbrales(moderado=30.0, alto=30.0).validar()
    assert any("estrictamente crecientes" in p for p in problemas)


def test_umbral_critico_fuera_de_rango() -> None:
    problemas = Umbrales(critico=501.0).validar()
    assert any("500" in p for p in problemas)


def test_ventana_invalida() -> None:
    problemas = Umbrales(ventana_horas=2).validar()
    assert any("ventana" in p.lower() for p in problemas)


def test_evaluar_critico() -> None:
    ev = evaluar(45.0, Umbrales())
    assert ev.nivel == "critico"
    assert ev.etiqueta == "Crítico"
    assert ev.excedente == 5.0
    assert ev.supera_critico is True
    assert ev.niveles_superados == ["moderado", "alto", "critico"]


def test_evaluar_sin_datos() -> None:
    ev = evaluar(None, Umbrales())
    assert ev.nivel == "sin_datos"
    assert ev.excedente is None
    assert ev.glifo == "○"
    assert "Sin dato" in ev.texto_excedente


def test_evaluar_margen_al_critico() -> None:
    ev = evaluar(25.0, Umbrales())
    assert ev.excedente == -15.0
    assert "Margen" in ev.texto_excedente


def test_resumen_por_nivel() -> None:
    evaluaciones = [evaluar(v, Umbrales()) for v in (None, 5, 25, 35, 45)]
    assert resumen_por_nivel(evaluaciones) == {
        "bajo": 1,
        "moderado": 1,
        "alto": 1,
        "critico": 1,
        "sin_datos": 1,
    }


def test_umbrales_como_lista() -> None:
    filas = Umbrales().como_lista()
    assert [f["nivel"] for f in filas] == ["bajo", "moderado", "alto", "critico"]
    assert filas[0]["rango"] == "0 a <20 mm/6 h"
    assert filas[-1]["rango"] == "≥40 mm/6 h"
