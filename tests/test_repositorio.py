"""Pruebas del repositorio en memoria (contrato de almacenamiento)."""

from __future__ import annotations

from satq.datos import AHORA, Alerta, CambioParametro, Comunicacion, Quebrada
from satq.motor import Umbrales
from satq.repositorio_memoria import RepositorioMemoria


def test_contenido_inicial() -> None:
    repo = RepositorioMemoria()
    assert len(repo.quebradas()) == 24
    assert len(repo.alertas()) == 7
    assert len(repo.comunicaciones()) == 3
    assert len(repo.historial_parametros()) == 2
    assert repo.umbrales().ventana_horas == 6


def test_agregar_lecturas() -> None:
    repo = RepositorioMemoria()
    antes = len(repo.quebradas()["quirio"].lecturas)
    repo.agregar_lecturas("quirio", [1.0, 2.0])
    assert len(repo.quebradas()["quirio"].lecturas) == antes + 2


def test_guardar_alerta_actualiza_y_agrega() -> None:
    repo = RepositorioMemoria()
    alerta = repo.alertas()[0]
    alerta.estado = "validada"
    repo.guardar_alerta(alerta)
    assert repo.alertas()[0].estado == "validada"

    nueva = Alerta("AL-0999", "quirio", AHORA, "alto", "pendiente", "prueba", 35.0)
    repo.guardar_alerta(nueva)
    assert len(repo.alertas()) == 8


def test_guardar_y_obtener_ingesta() -> None:
    repo = RepositorioMemoria()
    repo.guardar_ingesta("k", "huella", {"nivel": "alto"})
    assert repo.obtener_ingesta("k") == ("huella", {"nivel": "alto"})
    assert repo.obtener_ingesta("otra") is None


def test_crear_alerta_con_clave() -> None:
    repo = RepositorioMemoria()
    alerta = Alerta("AL-0998", "quirio", AHORA, "critico", "pendiente", "prueba", 45.0)
    repo.crear_alerta_con_clave(alerta, "k2", "huella2", {"creada": True})
    assert len(repo.alertas()) == 8
    assert repo.obtener_alerta_por_clave("k2") == ("huella2", {"creada": True})


def test_guardar_umbrales() -> None:
    repo = RepositorioMemoria()
    nuevos = Umbrales(critico=50.0)
    cambio = CambioParametro(AHORA, "Crítico: 50", "Diego Salazar")
    repo.guardar_umbrales(nuevos, [cambio])
    assert repo.umbrales().critico == 50.0
    assert repo.historial_parametros()[0] is cambio


def test_agregar_comunicaciones() -> None:
    repo = RepositorioMemoria()
    comunicacion = Comunicacion(AHORA, "quirio", 5, "SMS", "pendiente")
    repo.agregar_comunicaciones([comunicacion])
    assert repo.comunicaciones()[0] is comunicacion
    assert len(repo.comunicaciones()) == 4


def test_agregar_quebrada() -> None:
    repo = RepositorioMemoria()
    quebrada = Quebrada("nueva", "Nueva", "D", "P", "Lima", -12.0, -77.0)
    cambio = CambioParametro(AHORA, "Alta", "Diego Salazar")
    repo.agregar_quebrada(quebrada, cambio)
    assert "nueva" in repo.quebradas()
    assert repo.historial_parametros()[0] is cambio


def test_reiniciar_restituye_el_escenario() -> None:
    repo = RepositorioMemoria()
    repo.agregar_lecturas("quirio", [1.0])
    repo.guardar_ingesta("k", "huella", {"nivel": "alto"})
    repo.reiniciar()
    assert len(repo.alertas()) == 7
    assert repo.umbrales().critico == 40.0
    assert repo.obtener_ingesta("k") is None
