"""Vistas del SATQ Digital, independientes del framework web.

Cada función recibe el estado y un diccionario de parámetros, y devuelve
(nombre_de_plantilla, contexto). FastAPI (`satq.app`) y el servidor de
respaldo (`servidor_demo.py`) solo traducen peticiones HTTP a estas llamadas,
de modo que la lógica de presentación se prueba sin levantar un servidor.
"""

from __future__ import annotations

from datetime import datetime

from . import datos, graficos
from .datos import ESTADOS, PLANTILLAS, RESULTADOS
from .estado import Estado
from .motor import COLORES, ETIQUETAS, GLIFOS, NIVELES, Umbrales

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct",
         "nov", "dic"]


def fecha_larga(d: datetime) -> str:
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def fecha_hora(d: datetime) -> str:
    return f"{fecha_larga(d)} · {d.strftime('%H:%M')} PET"


def hora(d: datetime) -> str:
    return d.strftime("%H:%M")


def _base(estado: Estado, seccion: str) -> dict:
    """Contexto que comparten todas las pantallas con barra lateral."""
    conteo = estado.conteo_estados()
    return {
        "seccion": seccion,
        "usuario": estado.usuario,
        "ahora": estado.ahora,
        "ahora_texto": fecha_hora(estado.ahora),
        "alertas_activas": conteo["activas"],
        "umbrales": estado.umbrales,
        "etiquetas": ETIQUETAS,
        "glifos": GLIFOS,
        "colores": COLORES,
        "estados": ESTADOS,
        "resultados": RESULTADOS,
        "fecha_hora": fecha_hora,
        "fecha_larga": fecha_larga,
        "hora": hora,
    }


def _marcadores(estado: Estado, quebradas) -> list[dict]:
    salida = []
    for q in quebradas:
        ev = estado.evaluacion(q.codigo)
        salida.append(
            {
                "codigo": q.codigo,
                "nombre": q.nombre,
                "lat": q.lat,
                "lon": q.lon,
                "nivel": ev.nivel,
                "etiqueta": ev.etiqueta,
                "glifo": ev.glifo,
                "acumulado_texto": (
                    f"{ev.acumulado:g} mm/{estado.umbrales.ventana_horas} h"
                    if ev.acumulado is not None
                    else "sin dato"
                ),
            }
        )
    return salida


# --- Pantallas -------------------------------------------------------------


def login(estado: Estado, params: dict) -> tuple[str, dict]:
    return "login.html", {
        "error": params.get("error"),
        "correo": params.get("correo", "maria.torres@ejemplo.pe"),
    }


def dashboard(estado: Estado, params: dict) -> tuple[str, dict]:
    departamento = params.get("departamento") or ""
    provincia = params.get("provincia") or ""
    distrito = params.get("distrito") or ""
    seleccion = params.get("quebrada") or "huaycoloro"

    quebradas = estado.filtrar_quebradas(departamento, provincia, distrito)
    if seleccion not in {q.codigo for q in quebradas}:
        seleccion = quebradas[0].codigo if quebradas else ""

    ctx = _base(estado, "dashboard")
    q = estado.quebrada(seleccion)
    ev = estado.evaluacion(seleccion) if q else None

    serie = q.serie_acumulada(estado.umbrales.ventana_horas) if q else []
    ctx.update(
        {
            "titulo": "Monitoreo territorial",
            "quebradas": quebradas,
            "todas_quebradas": sorted(
                estado.quebradas.values(), key=lambda x: x.nombre
            ),
            "departamentos": estado.departamentos(),
            "provincias": estado.provincias(departamento or None),
            "distritos": estado.distritos(provincia or None),
            "filtros": {
                "departamento": departamento,
                "provincia": provincia,
                "distrito": distrito,
                "quebrada": seleccion,
            },
            "total_monitoreadas": len(estado.quebradas),
            "localidades_riesgo": estado.localidades_en_riesgo(),
            "conteo": estado.conteo_estados(),
            "mapa": graficos.mapa_peru(
                _marcadores(estado, quebradas),
                ancho=700,
                alto=430,
                destacado=seleccion,
            ),
            "alertas_recientes": estado.filtrar_alertas(estado=None)[:3],
            "quebrada_sel": q,
            "evaluacion": ev,
            "grafico": graficos.grafico_acumulado(
                q.horas() if q else [],
                serie,
                estado.umbrales.critico,
                estado.umbrales.ventana_horas,
            ),
            "serie_inicio": serie[-6] if len(serie) >= 6 else (serie[0] if serie else None),
            "serie_fin": serie[-1] if serie else None,
            "evaluaciones": estado.evaluaciones(),
        }
    )
    return "dashboard.html", ctx


def mapa(estado: Estado, params: dict) -> tuple[str, dict]:
    departamento = params.get("departamento") or ""
    provincia = params.get("provincia") or ""
    distrito = params.get("distrito") or ""
    busqueda = (params.get("buscar") or "").strip()
    seleccion = params.get("quebrada") or "huaycoloro"

    quebradas = estado.filtrar_quebradas(departamento, provincia, distrito)
    if busqueda:
        b = busqueda.lower()
        quebradas = [
            q
            for q in quebradas
            if b in q.nombre.lower()
            or b in q.distrito.lower()
            or b in q.departamento.lower()
        ] or quebradas

    if seleccion not in {q.codigo for q in quebradas}:
        seleccion = quebradas[0].codigo if quebradas else ""

    ctx = _base(estado, "mapa")
    q = estado.quebrada(seleccion)
    ev = estado.evaluacion(seleccion) if q else None
    ctx.update(
        {
            "titulo": "Mapa de riesgo",
            "quebradas": quebradas,
            "todas_quebradas": sorted(
                estado.quebradas.values(), key=lambda x: x.nombre
            ),
            "departamentos": estado.departamentos(),
            "provincias": estado.provincias(departamento or None),
            "distritos": estado.distritos(provincia or None),
            "filtros": {
                "departamento": departamento,
                "provincia": provincia,
                "distrito": distrito,
                "quebrada": seleccion,
                "buscar": busqueda,
            },
            "mapa": graficos.mapa_peru(
                _marcadores(estado, quebradas),
                ancho=720,
                alto=540,
                destacado=seleccion,
            ),
            "quebrada_sel": q,
            "evaluacion": ev,
            "capas": datos.CAPAS_MAPA,
        }
    )
    return "mapa.html", ctx


def quebrada(estado: Estado, params: dict) -> tuple[str, dict]:
    codigo = params.get("codigo") or "huaycoloro"
    q = estado.quebrada(codigo)
    if q is None:
        return "no_encontrado.html", _base(estado, "quebradas")

    ev = estado.evaluacion(codigo)
    serie = q.serie_acumulada(estado.umbrales.ventana_horas)
    historial = datos.historial_quebrada(codigo, estado.alertas)
    alerta_activa = next((a for a in historial if a.activa), None)

    ctx = _base(estado, "quebradas")
    ctx.update(
        {
            "titulo": f"Quebrada {q.nombre}",
            "quebrada_sel": q,
            "evaluacion": ev,
            "grafico": graficos.grafico_acumulado(
                q.horas(), serie, estado.umbrales.critico,
                estado.umbrales.ventana_horas, ancho=760, alto=260
            ),
            "serie": serie,
            "serie_inicio": serie[-6] if len(serie) >= 6 else (serie[0] if serie else None),
            "serie_fin": serie[-1] if serie else None,
            "historial": historial,
            "alerta_activa": alerta_activa,
            "recomendaciones": datos.RECOMENDACIONES,
        }
    )
    return "quebrada.html", ctx


def quebradas(estado: Estado, params: dict) -> tuple[str, dict]:
    departamento = params.get("departamento") or ""
    lista = estado.filtrar_quebradas(departamento)
    ctx = _base(estado, "quebradas")
    ctx.update(
        {
            "titulo": "Quebradas monitoreadas",
            "quebradas": lista,
            "evaluaciones": estado.evaluaciones(),
            "departamentos": estado.departamentos(),
            "filtros": {"departamento": departamento},
            "resumen": estado.resumen(),
        }
    )
    return "quebradas.html", ctx


def alertas(estado: Estado, params: dict) -> tuple[str, dict]:
    nivel = params.get("nivel") or ""
    departamento = params.get("departamento") or ""
    estado_f = params.get("estado") or "activas"
    seleccion = params.get("alerta") or ""

    lista = estado.filtrar_alertas(nivel or None, departamento or None, estado_f)
    if seleccion not in {a.codigo for a in lista}:
        seleccion = lista[0].codigo if lista else ""

    sel = estado.alerta(seleccion)
    ctx = _base(estado, "alertas")
    conteo = estado.conteo_estados()
    ctx.update(
        {
            "titulo": "Centro de alertas",
            "lista": lista,
            "conteo": conteo,
            "total_registros": len(estado.alertas),
            "niveles": NIVELES,
            "departamentos": estado.departamentos(),
            "filtros": {
                "nivel": nivel,
                "departamento": departamento,
                "estado": estado_f,
                "alerta": seleccion,
            },
            "seleccionada": sel,
            "quebrada_sel": estado.quebrada(sel.quebrada) if sel else None,
            "evaluacion_sel": (
                estado.evaluacion(sel.quebrada) if sel else None
            ),
            "mensaje": params.get("mensaje"),
            "quebradas": estado.quebradas,
        }
    )
    return "alertas.html", ctx


def notificaciones(estado: Estado, params: dict) -> tuple[str, dict]:
    codigo = params.get("quebrada") or "huaycoloro"
    plantilla = params.get("plantilla") or "preventivo"
    canales = params.get("canales") or ["WhatsApp", "SMS"]
    if isinstance(canales, str):
        canales = [canales]

    q = estado.quebrada(codigo) or estado.quebrada("huaycoloro")
    ctx = _base(estado, "notificaciones")
    ctx.update(
        {
            "titulo": "Gestión de notificaciones",
            "quebrada_sel": q,
            "todas_quebradas": sorted(
                estado.quebradas.values(), key=lambda x: x.nombre
            ),
            "plantillas": PLANTILLAS,
            "plantilla_sel": plantilla,
            "plantilla": PLANTILLAS.get(plantilla, PLANTILLAS["preventivo"]),
            "canales_sel": canales,
            "canales": datos.CANALES,
            "comunicaciones": estado.comunicaciones,
            "mensaje": params.get("mensaje"),
        }
    )
    return "notificaciones.html", ctx


def confirmacion(estado: Estado, params: dict) -> tuple[str, dict]:
    codigo = params.get("quebrada") or "huaycoloro"
    plantilla = params.get("plantilla") or "preventivo"
    canales = params.get("canales") or ["WhatsApp", "SMS"]
    if isinstance(canales, str):
        canales = [canales]

    q = estado.quebrada(codigo) or estado.quebrada("huaycoloro")
    ctx = _base(estado, "notificaciones")
    ctx.update(
        {
            "titulo": "Confirmación de envío",
            "quebrada_sel": q,
            "plantilla": PLANTILLAS.get(plantilla, PLANTILLAS["preventivo"]),
            "plantilla_sel": plantilla,
            "canales_sel": canales,
            "preparado": fecha_hora(estado.ahora),
        }
    )
    return "confirmacion.html", ctx


def reportes(estado: Estado, params: dict) -> tuple[str, dict]:
    resumen = estado.resumen()
    conteo = estado.conteo_estados()
    por_departamento: dict[str, dict[str, int]] = {}
    for cod, q in estado.quebradas.items():
        ev = estado.evaluacion(cod)
        fila = por_departamento.setdefault(
            q.departamento, {n: 0 for n in NIVELES} | {"total": 0}
        )
        fila[ev.nivel] = fila.get(ev.nivel, 0) + 1
        fila["total"] += 1

    ctx = _base(estado, "reportes")
    ctx.update(
        {
            "titulo": "Reportes del escenario",
            "resumen": resumen,
            "conteo": conteo,
            "por_departamento": dict(sorted(por_departamento.items())),
            "comunicaciones": estado.comunicaciones,
            "total_quebradas": len(estado.quebradas),
            "historial_parametros": estado.historial_parametros,
        }
    )
    return "reportes.html", ctx


def configuracion(estado: Estado, params: dict) -> tuple[str, dict]:
    codigo = params.get("quebrada") or "huaycoloro"
    pestana = params.get("pestana") or "umbrales"
    q = estado.quebrada(codigo) or estado.quebrada("huaycoloro")

    ctx = _base(estado, "configuracion")
    ctx.update(
        {
            "titulo": "Configuración y fuentes de datos",
            "quebrada_sel": q,
            "todas_quebradas": sorted(
                estado.quebradas.values(), key=lambda x: x.nombre
            ),
            "departamentos": estado.departamentos(),
            "provincias": estado.provincias(),
            "distritos": estado.distritos(),
            "filas_umbrales": estado.umbrales.como_lista(),
            "conectores": datos.CONECTORES,
            "canales": datos.CANALES,
            "historial_parametros": estado.historial_parametros,
            "pestana": pestana,
            "mensaje": params.get("mensaje"),
            "errores": params.get("errores") or [],
            "ventanas": [1, 3, 6, 12, 24],
            "tecnico": datos.USUARIOS["diego.salazar@ejemplo.pe"],
        }
    )
    return "configuracion.html", ctx


# --- Acciones (POST) -------------------------------------------------------


def accion_validar(estado: Estado, params: dict) -> str:
    codigo = params.get("alerta", "")
    a = estado.validar_alerta(codigo, estado.usuario["nombre"])
    if a:
        return f"/alertas?alerta={codigo}&mensaje=Alerta+{codigo}+validada+en+la+simulación"
    return "/alertas"


def accion_estado_alerta(estado: Estado, params: dict) -> str:
    codigo = params.get("alerta", "")
    nuevo = params.get("nuevo_estado", "")
    estado.cambiar_estado_alerta(codigo, nuevo, estado.usuario["nombre"])
    etiqueta = ESTADOS.get(nuevo, nuevo)
    return (
        f"/alertas?alerta={codigo}&estado=todas"
        f"&mensaje=Alerta+{codigo}+ahora+está+«{etiqueta}»+en+la+simulación"
    )


def accion_confirmar_envio(estado: Estado, params: dict) -> str:
    codigo = params.get("quebrada", "huaycoloro")
    canales = params.get("canales") or ["SMS"]
    if isinstance(canales, str):
        canales = [canales]
    q = estado.quebrada(codigo)
    destinatarios = q.destinatarios if q else 0
    estado.registrar_comunicacion(codigo, destinatarios, canales)
    return (
        f"/notificaciones?quebrada={codigo}"
        f"&mensaje=Registro+ficticio+creado+para+{len(canales)}+canal(es)."
        "+No+se+envió+ningún+mensaje"
    )


def accion_umbrales(estado: Estado, params: dict) -> tuple[str, list[str]]:
    try:
        nuevos = Umbrales(
            bajo=float(params.get("bajo", 0) or 0),
            moderado=float(params.get("moderado", 20) or 20),
            alto=float(params.get("alto", 30) or 30),
            critico=float(params.get("critico", 40) or 40),
            ventana_horas=int(params.get("ventana", 6) or 6),
        )
    except ValueError:
        return "", ["Los umbrales deben ser valores numéricos."]

    nuevos.unidad = f"mm / {nuevos.ventana_horas} h"
    problemas = estado.actualizar_umbrales(nuevos, estado.usuario["nombre"])
    if problemas:
        return "", problemas

    cambiadas = estado.recalcular_alertas()
    texto = "Umbrales guardados en la simulación"
    if cambiadas:
        texto += f".+{cambiadas}+alerta(s)+cambiaron+de+nivel+al+recalcular"
    return f"/configuracion?mensaje={texto.replace(' ', '+')}", []


def accion_nueva_quebrada(estado: Estado, params: dict) -> str:
    nombre = (params.get("nombre") or "").strip()
    if not nombre:
        return "/configuracion?mensaje=Indica+un+nombre+para+la+quebrada"
    q = estado.nueva_quebrada(
        nombre,
        (params.get("distrito") or "Sin distrito").strip(),
        (params.get("provincia") or "Sin provincia").strip(),
        (params.get("departamento") or "Lima").strip(),
    )
    return (
        f"/configuracion?quebrada={q.codigo}"
        f"&mensaje=Quebrada+«{q.nombre}»+registrada+sin+lecturas+asociadas"
    )
