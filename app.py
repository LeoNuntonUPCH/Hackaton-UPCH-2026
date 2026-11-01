"""SATQ Digital — aplicación FastAPI.

Este archivo es deliberadamente corto: solo traduce peticiones HTTP a
llamadas de `satq.vistas`. Toda la lógica vive en el paquete `satq`:

    satq/motor.py   → clasificación de riesgo (la regla del sistema)
    satq/datos.py   → escenario simulado
    satq/estado.py  → "base de datos" en memoria
    satq/graficos.py→ gráficos SVG generados en el servidor
    satq/vistas.py  → qué datos ve cada pantalla

Arranque:
    uvicorn app:app --reload --port 8000

Documentación automática de la API: http://127.0.0.1:8000/docs
"""

from __future__ import annotations

import math
import os
import time

from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from satq import observabilidad, vistas
from satq.estado import (
    ESTADO,
    AlertaNoRequerida,
    ConflictoAlerta,
    ConflictoIngesta,
)
from satq.motor import ETIQUETAS, clasificar
from satq.plantillas import DIR_ESTATICOS, render

app = FastAPI(
    title="SATQ Digital · API de demostración",
    version="1.0.0",
    description=(
        "Prototipo del Sistema de Alerta Temprana de Quebradas del Perú. "
        "Todos los datos son simulados y no deben usarse para decisiones "
        "de emergencia."
    ),
)

app.mount("/static", StaticFiles(directory=str(DIR_ESTATICOS)), name="static")

observabilidad.configurar_logs()


@app.middleware("http")
async def _medir_peticiones(request: Request, call_next) -> Response:
    inicio = time.perf_counter()
    try:
        respuesta = await call_next(request)
    except Exception:
        duracion = (time.perf_counter() - inicio) * 1000
        observabilidad.registrar_peticion(
            request.method, request.url.path, 500, duracion
        )
        raise
    duracion = (time.perf_counter() - inicio) * 1000
    observabilidad.registrar_peticion(
        request.method, request.url.path, respuesta.status_code, duracion
    )
    return respuesta


@app.get("/health", tags=["Observabilidad"])
def salud() -> JSONResponse:
    """Semáforo de salud del servicio y del almacenamiento."""
    datos = observabilidad.estado_salud()
    codigo = 200 if datos["estado"] == "ok" else 503
    return JSONResponse(status_code=codigo, content=datos)


@app.get("/api/metricas", tags=["Observabilidad"])
def metricas() -> dict:
    """Contadores acumulados de peticiones, errores y tiempos."""
    return observabilidad.resumen_metricas()


def _html(resultado: tuple[str, dict]) -> HTMLResponse:
    plantilla, contexto = resultado
    return HTMLResponse(render(plantilla, contexto))


def _params(request: Request) -> dict:
    """Convierte la cadena de consulta en un dict, con listas donde hace falta."""
    datos: dict = dict(request.query_params)
    multiples = request.query_params.getlist("canales")
    if multiples:
        datos["canales"] = multiples
    return datos


def _verificar_clave_n8n(x_api_key: str | None) -> None:
    clave_configurada = os.getenv("SATQ_INGESTA_API_KEY")
    if not clave_configurada:
        raise HTTPException(
            status_code=503,
            detail="La automatización no está configurada en este servidor.",
        )
    if x_api_key != clave_configurada:
        raise HTTPException(status_code=401, detail="API key inválida.")


# --- Pantallas -------------------------------------------------------------


@app.get("/", include_in_schema=False)
def raiz() -> RedirectResponse:
    return RedirectResponse("/login", status_code=303)


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def login(request: Request) -> HTMLResponse:
    return _html(vistas.login(ESTADO, _params(request)))


@app.post("/login", include_in_schema=False)
async def login_envio(request: Request) -> RedirectResponse:
    """Acceso de demostración: no autentica, solo elige el perfil a mostrar."""
    from satq.datos import USUARIOS

    formulario = await request.form()
    correo = str(formulario.get("correo", "")).strip().lower()
    ESTADO.usuario = USUARIOS.get(correo, USUARIOS["maria.torres@ejemplo.pe"])
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def dashboard(request: Request) -> HTMLResponse:
    return _html(vistas.dashboard(ESTADO, _params(request)))


@app.get("/mapa", response_class=HTMLResponse, include_in_schema=False)
def mapa(request: Request) -> HTMLResponse:
    return _html(vistas.mapa(ESTADO, _params(request)))


@app.get("/quebradas", response_class=HTMLResponse, include_in_schema=False)
def quebradas(request: Request) -> HTMLResponse:
    return _html(vistas.quebradas(ESTADO, _params(request)))


@app.get("/quebrada/{codigo}", response_class=HTMLResponse, include_in_schema=False)
def quebrada(codigo: str) -> HTMLResponse:
    return _html(vistas.quebrada(ESTADO, {"codigo": codigo}))


@app.get("/alertas", response_class=HTMLResponse, include_in_schema=False)
def alertas(request: Request) -> HTMLResponse:
    return _html(vistas.alertas(ESTADO, _params(request)))


@app.get("/notificaciones", response_class=HTMLResponse, include_in_schema=False)
def notificaciones(request: Request) -> HTMLResponse:
    return _html(vistas.notificaciones(ESTADO, _params(request)))


@app.get("/notificaciones/confirmar", response_class=HTMLResponse,
         include_in_schema=False)
def confirmar(request: Request) -> HTMLResponse:
    return _html(vistas.confirmacion(ESTADO, _params(request)))


@app.get("/reportes", response_class=HTMLResponse, include_in_schema=False)
def reportes(request: Request) -> HTMLResponse:
    return _html(vistas.reportes(ESTADO, _params(request)))


@app.get("/configuracion", response_class=HTMLResponse, include_in_schema=False)
def configuracion(request: Request) -> HTMLResponse:
    return _html(vistas.configuracion(ESTADO, _params(request)))


# --- Acciones --------------------------------------------------------------


@app.post("/alertas/validar", include_in_schema=False)
async def validar(request: Request) -> RedirectResponse:
    formulario = await request.form()
    destino = vistas.accion_validar(
        ESTADO, {"alerta": str(formulario.get("alerta", ""))}
    )
    return RedirectResponse(destino, status_code=303)


@app.post("/alertas/estado", include_in_schema=False)
async def cambiar_estado(request: Request) -> RedirectResponse:
    formulario = await request.form()
    destino = vistas.accion_estado_alerta(
        ESTADO,
        {
            "alerta": str(formulario.get("alerta", "")),
            "nuevo_estado": str(formulario.get("nuevo_estado", "")),
        },
    )
    return RedirectResponse(destino, status_code=303)


@app.post("/notificaciones/confirmar", include_in_schema=False)
async def confirmar_envio(request: Request) -> RedirectResponse:
    formulario = await request.form()
    destino = vistas.accion_confirmar_envio(
        ESTADO,
        {
            "quebrada": formulario.get("quebrada", "huaycoloro"),
            "canales": formulario.getlist("canales") or ["SMS"],
        },
    )
    return RedirectResponse(destino, status_code=303)


# `response_model=None` es necesario porque esta ruta devuelve dos tipos de
# respuesta distintos segun si los umbrales son validos. Sin ello, FastAPI
# intenta construir un modelo Pydantic a partir de la union y falla al
# importar el modulo.
@app.post("/configuracion/umbrales", include_in_schema=False, response_model=None)
async def guardar_umbrales(request: Request) -> Response:
    formulario = dict(await request.form())
    destino, errores = vistas.accion_umbrales(ESTADO, formulario)
    if errores:
        return _html(
            vistas.configuracion(ESTADO, {"errores": errores, "pestana": "umbrales"})
        )
    return RedirectResponse(destino, status_code=303)


@app.post("/configuracion/quebrada", include_in_schema=False)
async def registrar_quebrada(request: Request) -> RedirectResponse:
    formulario = dict(await request.form())
    return RedirectResponse(
        vistas.accion_nueva_quebrada(ESTADO, formulario), status_code=303
    )


# --- API JSON --------------------------------------------------------------
# Estos endpoints son los que muestran, ante una revisión, que hay un backend
# y no solo pantallas. Quedan documentados en /docs.


@app.get("/api/resumen", tags=["API"])
def api_resumen() -> dict:
    """Estado agregado del escenario: conteos por nivel y por estado de gestión."""
    return {
        "momento": ESTADO.ahora.isoformat(),
        "umbrales": {
            "moderado": ESTADO.umbrales.moderado,
            "alto": ESTADO.umbrales.alto,
            "critico": ESTADO.umbrales.critico,
            "ventana_horas": ESTADO.umbrales.ventana_horas,
        },
        "quebradas_monitoreadas": len(ESTADO.quebradas),
        "por_nivel": ESTADO.resumen(),
        "por_estado": ESTADO.conteo_estados(),
        "aviso": "Datos simulados. No usar para decisiones de emergencia.",
    }


@app.get("/api/quebradas", tags=["API"])
def api_quebradas() -> list[dict]:
    """Listado de quebradas con su acumulado y nivel calculado."""
    salida = []
    for codigo, q in ESTADO.quebradas.items():
        ev = ESTADO.evaluacion(codigo)
        salida.append(
            {
                "codigo": codigo,
                "nombre": q.nombre,
                "distrito": q.distrito,
                "provincia": q.provincia,
                "departamento": q.departamento,
                "lat": q.lat,
                "lon": q.lon,
                "acumulado_mm": ev.acumulado,
                "ventana_horas": ESTADO.umbrales.ventana_horas,
                "nivel": ev.nivel,
                "etiqueta": ev.etiqueta,
            }
        )
    return salida


@app.get("/api/quebradas/{codigo}", tags=["API"])
def api_quebrada(codigo: str) -> dict:
    """Serie de acumulado móvil y evaluación de una quebrada."""
    q = ESTADO.quebrada(codigo)
    if q is None:
        return {"error": "Quebrada no encontrada", "codigo": codigo}
    ev = ESTADO.evaluacion(codigo)
    ventana = ESTADO.umbrales.ventana_horas
    return {
        "codigo": codigo,
        "nombre": q.nombre,
        "ubicacion": q.ubicacion_larga,
        "serie": [
            {"hora": h.isoformat(), "acumulado_mm": v}
            for h, v in zip(q.horas(), q.serie_acumulada(ventana))
        ],
        "ventana_horas": ventana,
        "nivel": ev.nivel,
        "etiqueta": ev.etiqueta,
        "umbral_critico": ev.umbral_critico,
        "excedente_mm": ev.excedente,
    }


@app.get("/api/alertas", tags=["API"])
def api_alertas() -> list[dict]:
    """Alertas del escenario con su estado de gestión."""
    return [
        {
            "codigo": a.codigo,
            "quebrada": a.quebrada,
            "momento": a.momento.isoformat(),
            "nivel": a.nivel,
            "estado": a.estado,
            "fuente": a.fuente,
            "acumulado_mm": a.acumulado,
        }
        for a in ESTADO.alertas
    ]


@app.get("/api/evaluar", tags=["API"])
def api_evaluar(
    acumulado_mm: float = Query(..., description="Lluvia acumulada en la ventana"),
) -> dict:
    """Aplica el motor de umbrales a un valor cualquiera.

    Es el endpoint más útil para una revisión: permite comprobar la regla del
    sistema sin pasar por la interfaz.
    """
    nivel = clasificar(acumulado_mm, ESTADO.umbrales)
    return {
        "acumulado_mm": acumulado_mm,
        "ventana_horas": ESTADO.umbrales.ventana_horas,
        "nivel": nivel,
        "etiqueta": ETIQUETAS.get(nivel, "Sin datos"),
        "umbrales_vigentes": {
            "moderado": ESTADO.umbrales.moderado,
            "alto": ESTADO.umbrales.alto,
            "critico": ESTADO.umbrales.critico,
        },
    }


@app.post("/api/ingesta", tags=["API"])
async def api_ingesta(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict:
    """Recibe lecturas de lluvia desde n8n y devuelve la evaluación.

    No crea alertas: informa si el nivel exige una. La clave de idempotencia
    evita duplicar lecturas cuando el flujo se reintenta.
    """
    _verificar_clave_n8n(x_api_key)

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="El cuerpo debe ser JSON válido."
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400, detail="El cuerpo debe ser un objeto JSON."
        )

    quebrada = payload.get("quebrada")
    fuente = payload.get("fuente", "n8n")
    idempotency_key = payload.get("idempotency_key")
    lecturas_raw = payload.get("lecturas")

    if not isinstance(quebrada, str) or not quebrada.strip():
        raise HTTPException(status_code=400, detail="quebrada es obligatorio.")
    if not isinstance(fuente, str) or not fuente.strip():
        raise HTTPException(status_code=400, detail="fuente no puede estar vacío.")
    if not isinstance(idempotency_key, str) or not idempotency_key.strip():
        raise HTTPException(
            status_code=400, detail="idempotency_key es obligatorio."
        )
    if not isinstance(lecturas_raw, list) or not lecturas_raw:
        raise HTTPException(
            status_code=400, detail="lecturas debe ser una lista no vacía."
        )
    if len(lecturas_raw) > 100:
        raise HTTPException(
            status_code=400,
            detail="No se permiten más de 100 lecturas por envío.",
        )

    lecturas: list[float] = []
    for item in lecturas_raw:
        if not isinstance(item, dict) or "mm_h" not in item:
            raise HTTPException(
                status_code=400,
                detail="Cada lectura debe incluir mm_h.",
            )
        valor = item["mm_h"]
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise HTTPException(
                status_code=400,
                detail="Cada mm_h debe ser numérico.",
            )
        valor = float(valor)
        if not math.isfinite(valor) or valor < 0 or valor > 500:
            raise HTTPException(
                status_code=400,
                detail="Cada mm_h debe estar entre 0 y 500.",
            )
        lecturas.append(valor)

    try:
        return ESTADO.ingerir_lecturas(
            quebrada.strip(),
            lecturas,
            fuente.strip(),
            idempotency_key.strip(),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail="Quebrada no encontrada."
        ) from exc
    except ConflictoIngesta as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/alertas", tags=["API"])
async def api_crear_alerta(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> JSONResponse:
    """Crea una alerta si el nivel actual es alto o crítico.

    No crea otra alerta activa para la misma quebrada. La clave de idempotencia
    evita duplicarla cuando n8n reintenta el flujo.
    """
    _verificar_clave_n8n(x_api_key)

    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail="El cuerpo debe ser JSON válido."
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400, detail="El cuerpo debe ser un objeto JSON."
        )

    quebrada = payload.get("quebrada")
    fuente = payload.get("fuente", "n8n")
    idempotency_key = payload.get("idempotency_key")

    if not isinstance(quebrada, str) or not quebrada.strip():
        raise HTTPException(status_code=400, detail="quebrada es obligatorio.")
    if not isinstance(fuente, str) or not fuente.strip():
        raise HTTPException(status_code=400, detail="fuente no puede estar vacío.")
    if not isinstance(idempotency_key, str) or not idempotency_key.strip():
        raise HTTPException(
            status_code=400, detail="idempotency_key es obligatorio."
        )

    try:
        resultado = ESTADO.crear_alerta_si_corresponde(
            quebrada.strip(),
            fuente.strip(),
            idempotency_key.strip(),
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404, detail="Quebrada no encontrada."
        ) from exc
    except ConflictoAlerta as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AlertaNoRequerida as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    estado_http = (
        201
        if resultado.get("creada") and not resultado.get("duplicado")
        else 200
    )
    return JSONResponse(status_code=estado_http, content=resultado)


@app.post("/api/reiniciar", tags=["API"])
def api_reiniciar() -> dict:
    """Devuelve el escenario a su punto inicial. Útil entre demostraciones."""
    ESTADO.reiniciar()
    return {"reiniciado": True, "momento": ESTADO.ahora.isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
