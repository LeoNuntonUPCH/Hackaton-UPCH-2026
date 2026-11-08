"""Métricas de evaluación observacional para el prototipo SATQ Digital."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class AlertaEmitida:
    """Inicio de un episodio de alerta para una quebrada."""

    quebrada: str
    instante: datetime


@dataclass(frozen=True)
class EventoObservado:
    """Instante documentado de un evento en una quebrada."""

    quebrada: str
    instante: datetime
    fuente: str = ""
    referencia: str = ""


@dataclass(frozen=True)
class LecturaLluvia:
    """Lectura de una estación con procedencia rastreable."""

    estacion: str
    instante: datetime
    precipitacion_mm: float | None
    fuente: str
    referencia: str


@dataclass(frozen=True)
class MetricasEventos:
    """Métricas por episodio; proporciones indefinidas se representan como None."""

    aciertos: int
    eventos_omitidos: int
    falsas_alarmas: int
    pod: float | None
    far: float | None
    csi: float | None
    anticipacion_media_min: float | None


def cargar_eventos_csv(ruta: str | Path) -> list[EventoObservado]:
    """Carga eventos documentados; cada fila debe citar una fuente verificable."""
    campos_requeridos = {"quebrada", "instante", "fuente", "referencia"}
    eventos: list[EventoObservado] = []
    claves_vistas: set[tuple[str, datetime]] = set()

    with Path(ruta).open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        encabezados = lector.fieldnames or []
        if len(encabezados) != len(set(encabezados)):
            raise ValueError("El CSV contiene encabezados duplicados.")
        faltantes = campos_requeridos.difference(encabezados)
        if faltantes:
            raise ValueError(
                "Faltan columnas requeridas: " + ", ".join(sorted(faltantes))
            )

        for numero_fila, fila in enumerate(lector, start=2):
            if None in fila:
                raise ValueError(
                    f"Fila {numero_fila}: contiene columnas adicionales sin encabezado."
                )
            quebrada = (fila.get("quebrada") or "").strip()
            instante_txt = (fila.get("instante") or "").strip()
            fuente = (fila.get("fuente") or "").strip()
            referencia = (fila.get("referencia") or "").strip()
            if not all((quebrada, instante_txt, fuente, referencia)):
                raise ValueError(
                    f"Fila {numero_fila}: quebrada, instante, fuente y referencia son obligatorios."
                )
            try:
                instante = datetime.fromisoformat(instante_txt.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(
                    f"Fila {numero_fila}: instante debe usar formato ISO 8601."
                ) from exc
            if instante.tzinfo is None or instante.utcoffset() is None:
                raise ValueError(f"Fila {numero_fila}: instante debe incluir zona horaria.")
            instante = instante.astimezone(timezone.utc)

            clave = (quebrada, instante)
            if clave in claves_vistas:
                raise ValueError(f"Fila {numero_fila}: evento duplicado para quebrada e instante.")
            claves_vistas.add(clave)
            eventos.append(EventoObservado(quebrada, instante, fuente, referencia))

    return eventos


def cargar_lecturas_csv(ruta: str | Path) -> list[LecturaLluvia]:
    """Carga CSV normalizado y rechaza fechas ambiguas o mediciones inválidas.

    El esquema requiere ``estacion``, ``instante``, ``precipitacion_mm``,
    ``fuente`` y ``referencia``. Los faltantes de precipitación se preservan
    como ``None``; nunca se convierten en lluvia cero.
    """
    campos_requeridos = {
        "estacion",
        "instante",
        "precipitacion_mm",
        "fuente",
        "referencia",
    }
    lecturas: list[LecturaLluvia] = []
    claves_vistas: set[tuple[str, datetime]] = set()

    with Path(ruta).open("r", encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        encabezados = lector.fieldnames or []
        if len(encabezados) != len(set(encabezados)):
            raise ValueError("El CSV contiene encabezados duplicados.")
        faltantes = campos_requeridos.difference(encabezados)
        if faltantes:
            raise ValueError(
                "Faltan columnas requeridas: " + ", ".join(sorted(faltantes))
            )

        for numero_fila, fila in enumerate(lector, start=2):
            if None in fila:
                raise ValueError(
                    f"Fila {numero_fila}: contiene columnas adicionales sin encabezado."
                )
            estacion = (fila.get("estacion") or "").strip()
            instante_txt = (fila.get("instante") or "").strip()
            fuente = (fila.get("fuente") or "").strip()
            referencia = (fila.get("referencia") or "").strip()
            if not all((estacion, instante_txt, fuente, referencia)):
                raise ValueError(
                    f"Fila {numero_fila}: estación, instante, fuente y referencia son obligatorios."
                )

            try:
                instante = datetime.fromisoformat(instante_txt.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(
                    f"Fila {numero_fila}: instante debe usar formato ISO 8601."
                ) from exc
            if instante.tzinfo is None or instante.utcoffset() is None:
                raise ValueError(f"Fila {numero_fila}: instante debe incluir zona horaria.")
            instante = instante.astimezone(timezone.utc)

            clave = (estacion, instante)
            if clave in claves_vistas:
                raise ValueError(f"Fila {numero_fila}: lectura duplicada para estación e instante.")
            claves_vistas.add(clave)

            precipitacion_txt = (fila.get("precipitacion_mm") or "").strip()
            if precipitacion_txt.casefold() in {"", "na", "n/a", "null"}:
                precipitacion = None
            else:
                try:
                    precipitacion = float(precipitacion_txt)
                except ValueError as exc:
                    raise ValueError(
                        f"Fila {numero_fila}: precipitación debe ser numérica o faltante."
                    ) from exc
                if not math.isfinite(precipitacion) or precipitacion < 0:
                    raise ValueError(
                        f"Fila {numero_fila}: precipitación debe ser finita y no negativa."
                    )

            lecturas.append(
                LecturaLluvia(
                    estacion=estacion,
                    instante=instante,
                    precipitacion_mm=precipitacion,
                    fuente=fuente,
                    referencia=referencia,
                )
            )

    return lecturas


def evaluar_eventos(
    alertas: Iterable[AlertaEmitida],
    eventos: Iterable[EventoObservado],
    ventana_anticipacion_min: int = 360,
) -> MetricasEventos:
    """Empareja alertas y eventos de la misma quebrada, como máximo una vez.

    Una alerta es acierto si comenzó entre cero y ``ventana_anticipacion_min``
    antes del evento. Si hay varias candidatas, se usa primero la alerta más
    antigua para conservar candidatas recientes para eventos posteriores.
    """
    if ventana_anticipacion_min < 0:
        raise ValueError("La ventana de anticipación no puede ser negativa.")
    lista_alertas = list(alertas)
    lista_eventos = list(eventos)
    if any(
        alerta.instante.tzinfo is None or alerta.instante.utcoffset() is None
        for alerta in lista_alertas
    ) or any(
        evento.instante.tzinfo is None or evento.instante.utcoffset() is None
        for evento in lista_eventos
    ):
        raise ValueError("Todos los instantes deben incluir zona horaria.")

    lista_alertas.sort(key=lambda alerta: alerta.instante)
    lista_eventos.sort(key=lambda evento: evento.instante)
    usadas: set[int] = set()
    anticipaciones: list[float] = []

    for evento in lista_eventos:
        candidatas_validas = [
            (alerta.instante, lead, indice)
            for indice, alerta in enumerate(lista_alertas)
            if indice not in usadas
            and alerta.quebrada == evento.quebrada
            for lead in [(evento.instante - alerta.instante).total_seconds() / 60]
            if 0 <= lead <= ventana_anticipacion_min
        ]
        if candidatas_validas:
            _, lead, indice = min(candidatas_validas)
            usadas.add(indice)
            anticipaciones.append(lead)

    aciertos = len(usadas)
    omitidos = len(lista_eventos) - aciertos
    falsas_alarmas = len(lista_alertas) - aciertos
    total_eventos = aciertos + omitidos
    alertas_con_resultado = aciertos + falsas_alarmas
    union = aciertos + omitidos + falsas_alarmas

    return MetricasEventos(
        aciertos=aciertos,
        eventos_omitidos=omitidos,
        falsas_alarmas=falsas_alarmas,
        pod=aciertos / total_eventos if total_eventos else None,
        far=falsas_alarmas / alertas_con_resultado if alertas_con_resultado else None,
        csi=aciertos / union if union else None,
        anticipacion_media_min=(
            sum(anticipaciones) / len(anticipaciones) if anticipaciones else None
        ),
    )
