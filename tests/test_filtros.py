"""Filtro territorial: jerarquía, dependencia entre niveles y combinaciones."""

from __future__ import annotations

from satq import vistas
from satq.estado import Estado
from satq.plantillas import render


def test_jerarquia_coherente(estado: Estado) -> None:
    """Cada provincia tiene un único departamento y cada distrito una única provincia."""
    dep_de_provincia: dict[str, set[str]] = {}
    pro_de_distrito: dict[tuple[str, str], set[str]] = {}
    for q in estado.quebradas.values():
        dep_de_provincia.setdefault(q.provincia, set()).add(q.departamento)
        pro_de_distrito.setdefault((q.departamento, q.distrito), set()).add(q.provincia)
    assert all(len(v) == 1 for v in dep_de_provincia.values())
    assert all(len(v) == 1 for v in pro_de_distrito.values())


def test_catalogo_sin_anexos_como_distrito(estado: Estado) -> None:
    distritos = {q.distrito for q in estado.quebradas.values()}
    assert not distritos & {"Chosica", "Jicamarca", "Huachipa"}


def test_distritos_respetan_departamento(estado: Estado) -> None:
    assert estado.distritos(departamento="Piura") == ["Castilla", "Chulucanas", "Cura Mori"]
    assert estado.distritos("Lima", "Lima") == ["Ate", "Chaclacayo", "Lurigancho-Chosica"]


def test_normalizar_descarta_hijos_ajenos(estado: Estado) -> None:
    f = estado.normalizar_ubicacion("Piura", "Lima", "Ate", "huaycoloro")
    assert f == {"departamento": "Piura", "provincia": "", "distrito": "", "quebrada": ""}


def test_normalizar_conserva_combinacion_valida(estado: Estado) -> None:
    f = estado.normalizar_ubicacion("Lima", "Huarochirí", "San Antonio", "san-antonio")
    assert f["quebrada"] == "san-antonio"
    assert f["distrito"] == "San Antonio"


def test_todos_mas_un_valor(estado: Estado) -> None:
    _, ctx = vistas.dashboard(estado, {"provincia": "Trujillo"})
    assert {q.provincia for q in ctx["quebradas"]} == {"Trujillo"}
    assert ctx["total_monitoreadas"] == len(ctx["quebradas"])


def test_tarjetas_y_alertas_siguen_el_filtro(estado: Estado) -> None:
    _, ctx = vistas.dashboard(estado, {"departamento": "Piura"})
    assert ctx["total_monitoreadas"] == 4
    deps = {estado.quebradas[a.quebrada].departamento for a in ctx["alertas_recientes"]}
    assert deps <= {"Piura"}
    activas = sum(
        1 for a in estado.alertas
        if a.activa and estado.quebradas[a.quebrada].departamento == "Piura"
    )
    assert ctx["activas_ambito"] == activas


def test_quebrada_elegida_acota_el_ambito(estado: Estado) -> None:
    _, ctx = vistas.dashboard(estado, {"quebrada": "castilla"})
    assert [q.codigo for q in ctx["quebradas"]] == ["castilla"]
    assert all(a.quebrada == "castilla" for a in ctx["alertas_recientes"])


def test_busqueda_sin_coincidencias_queda_vacia(estado: Estado) -> None:
    plantilla, ctx = vistas.mapa(estado, {"buscar": "zzzz"})
    assert ctx["quebradas"] == []
    html = render(plantilla, ctx)
    assert "Sin coincidencias" in html
    assert "Limpiar filtros" in html


def test_alertas_filtran_por_provincia_y_distrito(estado: Estado) -> None:
    _, ctx = vistas.alertas(
        estado, {"departamento": "Lima", "provincia": "Lima", "distrito": "Ate", "estado": "todas"}
    )
    assert all(estado.quebradas[a.quebrada].distrito == "Ate" for a in ctx["lista"])


def test_enlaces_conservan_el_filtro(estado: Estado) -> None:
    plantilla, ctx = vistas.dashboard(estado, {"departamento": "La Libertad"})
    html = render(plantilla, ctx)
    assert "/mapa?departamento=La%20Libertad" in html
    assert "/alertas?estado=todas&departamento=La%20Libertad" in html


def test_alta_rechaza_provincia_de_otro_departamento(estado: Estado) -> None:
    antes = len(estado.quebradas)
    destino = vistas.accion_nueva_quebrada(
        estado, {"nombre": "Q", "departamento": "Piura", "provincia": "Lima", "distrito": "Ate"}
    )
    assert "error=" in destino
    assert len(estado.quebradas) == antes


def test_alta_exige_todos_los_niveles(estado: Estado) -> None:
    destino = vistas.accion_nueva_quebrada(
        estado, {"nombre": "Q", "departamento": "Lima", "provincia": "", "distrito": ""}
    )
    assert "error=" in destino
