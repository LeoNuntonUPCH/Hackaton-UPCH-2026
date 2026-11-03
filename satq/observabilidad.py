"""Observabilidad mínima: logs, métricas y estado de salud.

Solo usa la librería estándar. Los contadores viven en memoria y vuelven a cero
cuando reinicia el proceso, igual que el resto del estado de la demo.
"""

from __future__ import annotations

import json
import logging
import os
import time
from threading import RLock
from typing import Any

_REGISTRO = logging.getLogger("satq")
_INICIO = time.monotonic()
_CANDADO = RLock()

_METRICAS: dict[str, Any] = {
    "peticiones_total": 0,
    "errores_5xx": 0,
    "peticiones_por_ruta": {},
    "duracion_total_ms": 0.0,
    "duracion_max_ms": 0.0,
    "ultima_peticion": None,
}


def configurar_logs(nivel: str | None = None) -> None:
    """Configura un logger con una línea JSON por evento (idempotente)."""
    if getattr(_REGISTRO, "_satq_configurado", False):
        return
    manejador = logging.StreamHandler()
    manejador.setFormatter(logging.Formatter("%(message)s"))
    _REGISTRO.addHandler(manejador)
    nombre = (nivel or os.environ.get("SATQ_LOG_LEVEL", "INFO")).upper()
    _REGISTRO.setLevel(getattr(logging, nombre, logging.INFO))
    _REGISTRO.propagate = False
    setattr(_REGISTRO, "_satq_configurado", True)


def reiniciar_metricas() -> None:
    """Reinicia los contadores (útil para pruebas y para volver a empezar)."""
    with _CANDADO:
        _METRICAS["peticiones_total"] = 0
        _METRICAS["errores_5xx"] = 0
        _METRICAS["peticiones_por_ruta"] = {}
        _METRICAS["duracion_total_ms"] = 0.0
        _METRICAS["duracion_max_ms"] = 0.0
        _METRICAS["ultima_peticion"] = None


def registrar_peticion(
    metodo: str, ruta: str, estado: int, duracion_ms: float
) -> None:
    """Suma una petición a las métricas y emite un log estructurado."""
    with _CANDADO:
        _METRICAS["peticiones_total"] += 1
        if estado >= 500:
            _METRICAS["errores_5xx"] += 1
        por_ruta: dict[str, int] = _METRICAS["peticiones_por_ruta"]
        clave = f"{metodo} {ruta}"
        por_ruta[clave] = por_ruta.get(clave, 0) + 1
        _METRICAS["duracion_total_ms"] += duracion_ms
        _METRICAS["duracion_max_ms"] = max(_METRICAS["duracion_max_ms"], duracion_ms)
        _METRICAS["ultima_peticion"] = {
            "metodo": metodo,
            "ruta": ruta,
            "estado": estado,
            "ms": round(duracion_ms, 2),
        }

    evento = {
        "evento": "peticion",
        "metodo": metodo,
        "ruta": ruta,
        "estado": estado,
        "ms": round(duracion_ms, 2),
    }
    linea = json.dumps(evento, ensure_ascii=False)
    if estado >= 500:
        _REGISTRO.error(linea)
    elif estado >= 400:
        _REGISTRO.warning(linea)
    else:
        _REGISTRO.info(linea)


def resumen_metricas() -> dict[str, Any]:
    """Fotografía de los contadores acumulados."""
    with _CANDADO:
        total = _METRICAS["peticiones_total"]
        duracion_total = _METRICAS["duracion_total_ms"]
        return {
            "peticiones_total": total,
            "errores_5xx": _METRICAS["errores_5xx"],
            "peticiones_por_ruta": dict(_METRICAS["peticiones_por_ruta"]),
            "duracion_promedio_ms": round(duracion_total / total, 2) if total else 0.0,
            "duracion_max_ms": round(_METRICAS["duracion_max_ms"], 2),
            "ultima_peticion": _METRICAS["ultima_peticion"],
            "uptime_s": round(time.monotonic() - _INICIO, 1),
        }


def estado_base_datos() -> dict[str, Any]:
    """Indica el modo de almacenamiento y, si aplica, si PostgreSQL responde."""
    from . import almacen_postgres

    if not almacen_postgres.habilitado():
        return {"modo": "memoria", "conectada": None}
    try:
        with almacen_postgres._conectar() as conexion, conexion.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:
        return {"modo": "postgres", "conectada": False, "error": str(exc)}
    return {"modo": "postgres", "conectada": True}


def estado_salud() -> dict[str, Any]:
    """Semáforo de salud para el endpoint /health."""
    from mensajeria import maximo_envios, modo_real, proveedor_configurado

    base = estado_base_datos()
    saludable = base["conectada"] is not False
    resumen = resumen_metricas()
    return {
        "estado": "ok" if saludable else "degradado",
        "base_datos": base,
        "mensajeria": {
            "modo": "real" if modo_real() else "simulado",
            "proveedor": proveedor_configurado() or "sin proveedor",
            "max_envios": maximo_envios(),
        },
        "uptime_s": resumen["uptime_s"],
        "peticiones_total": resumen["peticiones_total"],
        "errores_5xx": resumen["errores_5xx"],
    }
