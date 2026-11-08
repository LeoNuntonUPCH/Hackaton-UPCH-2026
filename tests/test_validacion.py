"""Pruebas de la evaluación observacional de alertas."""

from datetime import datetime, timezone

import pytest

from satq.validacion import (
    AlertaEmitida,
    EventoObservado,
    cargar_eventos_csv,
    cargar_lecturas_csv,
    evaluar_eventos,
)


def test_evaluar_eventos_calcula_aciertos_fallos_y_falsas_alarmas() -> None:
    alertas = [
        AlertaEmitida("Huaycoloro", datetime(2023, 3, 12, 16, 0, tzinfo=timezone.utc)),
        AlertaEmitida("Huaycoloro", datetime(2023, 3, 12, 22, 0, tzinfo=timezone.utc)),
    ]
    eventos = [
        EventoObservado("Huaycoloro", datetime(2023, 3, 12, 18, 0, tzinfo=timezone.utc)),
        EventoObservado("Río Seco", datetime(2023, 3, 12, 20, 0, tzinfo=timezone.utc)),
    ]

    metricas = evaluar_eventos(alertas, eventos, ventana_anticipacion_min=360)

    assert metricas.aciertos == 1
    assert metricas.eventos_omitidos == 1
    assert metricas.falsas_alarmas == 1
    assert metricas.pod == 0.5
    assert metricas.far == 0.5
    assert metricas.csi == 1 / 3
    assert metricas.anticipacion_media_min == 120


def test_evaluar_eventos_rechaza_ventana_de_anticipacion_negativa() -> None:
    with pytest.raises(ValueError, match="no puede ser negativa"):
        evaluar_eventos([], [], ventana_anticipacion_min=-1)


def test_evaluar_eventos_rechaza_fechas_sin_zona_horaria() -> None:
    alertas = [AlertaEmitida("Huaycoloro", datetime(2023, 3, 12, 10, 0))]
    eventos = [EventoObservado("Huaycoloro", datetime(2023, 3, 12, 12, 0))]

    with pytest.raises(ValueError, match="zona horaria"):
        evaluar_eventos(alertas, eventos)


def test_evaluar_eventos_maximiza_emparejamientos_uno_a_uno() -> None:
    alertas = [
        AlertaEmitida("Huaycoloro", datetime(2023, 3, 12, 6, 30, tzinfo=timezone.utc)),
        AlertaEmitida("Huaycoloro", datetime(2023, 3, 12, 10, 0, tzinfo=timezone.utc)),
    ]
    eventos = [
        EventoObservado("Huaycoloro", datetime(2023, 3, 12, 12, 0, tzinfo=timezone.utc)),
        EventoObservado("Huaycoloro", datetime(2023, 3, 12, 16, 0, tzinfo=timezone.utc)),
    ]

    metricas = evaluar_eventos(alertas, eventos, ventana_anticipacion_min=360)

    assert metricas.aciertos == 2
    assert metricas.eventos_omitidos == 0
    assert metricas.falsas_alarmas == 0
    assert metricas.anticipacion_media_min == 345


def test_cargar_lecturas_csv_conserva_faltantes_y_procedencia(tmp_path) -> None:
    ruta = tmp_path / "lluvia.csv"
    ruta.write_text(
        "estacion,instante,precipitacion_mm,fuente,referencia\n"
        "CHOSICA,2023-03-12T10:00:00-05:00,0.4,SENAMHI,https://senamhi.gob.pe/datos\n"
        "CHOSICA,2023-03-12T11:00:00-05:00,,SENAMHI,https://senamhi.gob.pe/datos\n",
        encoding="utf-8",
    )

    lecturas = cargar_lecturas_csv(ruta)

    assert len(lecturas) == 2
    assert lecturas[0].estacion == "CHOSICA"
    assert lecturas[0].instante == datetime(2023, 3, 12, 15, 0, tzinfo=timezone.utc)
    assert lecturas[0].precipitacion_mm == 0.4
    assert lecturas[1].precipitacion_mm is None
    assert lecturas[1].fuente == "SENAMHI"
    assert lecturas[1].referencia == "https://senamhi.gob.pe/datos"


def test_cargar_eventos_csv_exige_y_conserva_fuente(tmp_path) -> None:
    ruta = tmp_path / "eventos.csv"
    ruta.write_text(
        "quebrada,instante,fuente,referencia\n"
        "Huaycoloro,2023-03-12T17:44:00-05:00,INDECI,https://indeci.gob.pe/reporte.pdf\n",
        encoding="utf-8",
    )

    eventos = cargar_eventos_csv(ruta)

    assert eventos == [
        EventoObservado(
            "Huaycoloro",
            datetime(2023, 3, 12, 22, 44, tzinfo=timezone.utc),
            "INDECI",
            "https://indeci.gob.pe/reporte.pdf",
        )
    ]
