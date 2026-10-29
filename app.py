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

from fastapi import FastAPI, Query, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from satq import vistas
from satq.estado import ESTADO
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


@app.post("/api/reiniciar", tags=["API"])
def api_reiniciar() -> dict:
    """Devuelve el escenario a su punto inicial. Útil entre demostraciones."""
    ESTADO.reiniciar()
    return {"reiniciado": True, "momento": ESTADO.ahora.isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
