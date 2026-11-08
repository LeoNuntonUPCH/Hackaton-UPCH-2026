"""Vistas del SATQ Digital, independientes del framework web.

Cada función recibe el estado y un diccionario de parámetros, y devuelve
(nombre_de_plantilla, contexto). FastAPI (`satq.app`) y el servidor de
respaldo (`servidor_demo.py`) solo traducen peticiones HTTP a estas llamadas,
de modo que la lógica de presentación se prueba sin levantar un servidor.
"""

from __future__ import annotations

from datetime import datetime
from urllib.parse import quote_plus

from mensajeria import modo_real, proveedor_configurado

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


def _mascarar_telefono(telefono: str) -> str:
    if not telefono:
        return ""
    if len(telefono) <= 7:
        return "****"
    return f"{telefono[:3]}****{telefono[-4:]}"


def _base(estado: Estado, seccion: str) -> dict:
    """Contexto que comparten todas las pantallas con barra lateral."""
    conteo = estado.conteo_estados()
    ahora = datos.ahora_peru()
    return {
        "seccion": seccion,
        "usuario": estado.usuario,
        "ahora": ahora,
        "ahora_texto": fecha_hora(ahora),
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


def _filtros_ubicacion(estado: Estado, params: dict) -> dict[str, str]:
    """Lee los cuatro niveles territoriales y descarta los incoherentes."""
    return estado.normalizar_ubicacion(
        (params.get("departamento") or "").strip(),
        (params.get("provincia") or "").strip(),
        (params.get("distrito") or "").strip(),
        (params.get("quebrada") or "").strip(),
    )


def _ambito(estado: Estado, filtros: dict[str, str]) -> list:
    """Quebradas que cubre el filtro: la elegida o todas las del territorio."""
    quebradas = estado.filtrar_quebradas(
        filtros["departamento"], filtros["provincia"], filtros["distrito"]
    )
    if filtros["quebrada"]:
        quebradas = [q for q in quebradas if q.codigo == filtros["quebrada"]]
    return quebradas


def _detalle(quebradas: list) -> str:
    """Quebrada que se muestra en el gráfico: Huaycoloro si está, o la primera."""
    codigos = [q.codigo for q in quebradas]
    if "huaycoloro" in codigos:
        return "huaycoloro"
    return codigos[0] if codigos else ""


def dashboard(estado: Estado, params: dict) -> tuple[str, dict]:
    filtros = _filtros_ubicacion(estado, params)
    quebradas = _ambito(estado, filtros)
    codigos = {q.codigo for q in quebradas}
    seleccion = filtros["quebrada"] or _detalle(quebradas)

    ctx = _base(estado, "dashboard")
    q = estado.quebrada(seleccion) if seleccion else None
    ev = estado.evaluacion(seleccion) if q else None

    # Tarjetas y alertas recientes se calculan sobre el ámbito filtrado.
    alertas_ambito = [a for a in estado.alertas if a.quebrada in codigos]
    evaluaciones = estado.evaluaciones()
    en_riesgo = sum(
        1
        for c in codigos
        if c in evaluaciones
        and evaluaciones[c].nivel in ("moderado", "alto", "critico")
    )
    recientes = estado.filtrar_alertas(
        departamento=filtros["departamento"] or None,
        provincia=filtros["provincia"] or None,
        distrito=filtros["distrito"] or None,
        quebrada=filtros["quebrada"] or None,
    )

    serie = q.serie_acumulada(estado.umbrales.ventana_horas) if q else []
    ctx.update(
        {
            "titulo": "Monitoreo territorial",
            "quebradas": quebradas,
            "todas_quebradas": sorted(
                estado.quebradas.values(), key=lambda x: x.nombre
            ),
            "jerarquia": estado.jerarquia(),
            "filtros": filtros,
            "hay_filtro": any(filtros.values()),
            "total_monitoreadas": len(quebradas),
            "localidades_riesgo": en_riesgo,
            "activas_ambito": sum(1 for a in alertas_ambito if a.activa),
            "conteo": estado.conteo_estados(),
            "mapa": graficos.mapa_peru(
                _marcadores(estado, quebradas),
                ancho=700,
                alto=430,
                destacado=seleccion,
            ),
            "alertas_recientes": recientes[:3],
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
            "evaluaciones": evaluaciones,
        }
    )
    return "dashboard.html", ctx


def mapa(estado: Estado, params: dict) -> tuple[str, dict]:
    filtros = _filtros_ubicacion(estado, params)
    busqueda = (params.get("buscar") or "").strip()

    quebradas = _ambito(estado, filtros)
    if busqueda:
        b = busqueda.lower()
        # Sin coincidencias la lista queda vacía: la pantalla lo avisa.
        quebradas = [
            q
            for q in quebradas
            if b in q.nombre.lower()
            or b in q.distrito.lower()
            or b in q.provincia.lower()
            or b in q.departamento.lower()
        ]

    seleccion = filtros["quebrada"] or _detalle(quebradas)

    ctx = _base(estado, "mapa")
    q = estado.quebrada(seleccion) if seleccion else None
    ev = estado.evaluacion(seleccion) if q else None
    ctx.update(
        {
            "titulo": "Mapa de riesgo",
            "quebradas": quebradas,
            "todas_quebradas": sorted(
                estado.quebradas.values(), key=lambda x: x.nombre
            ),
            "jerarquia": estado.jerarquia(),
            "filtros": {**filtros, "buscar": busqueda},
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
    ubicacion = _filtros_ubicacion(estado, params)
    estado_f = params.get("estado") or "activas"
    seleccion = params.get("alerta") or ""

    lista = estado.filtrar_alertas(
        nivel or None,
        ubicacion["departamento"] or None,
        estado_f,
        provincia=ubicacion["provincia"] or None,
        distrito=ubicacion["distrito"] or None,
        quebrada=ubicacion["quebrada"] or None,
    )
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
            "jerarquia": estado.jerarquia(),
            "filtros": {
                "nivel": nivel,
                **ubicacion,
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
            "sms_modo": "real" if modo_real() else "simulado",
            "sms_proveedor": proveedor_configurado() or "sin proveedor",
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
            "sms_modo": "real" if modo_real() else "simulado",
            "sms_proveedor": proveedor_configurado() or "sin proveedor",
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
            "sms_modo": "real" if modo_real() else "simulado",
            "sms_proveedor": proveedor_configurado() or "sin proveedor",
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
            "errores": params.get("errores")
            or ([params["error"]] if params.get("error") else []),
            "ventanas": [1, 3, 6, 12, 24],
            "tecnico": datos.USUARIOS["diego.salazar@ejemplo.pe"],
        }
    )
    return "configuracion.html", ctx


def suscripcion(estado: Estado, params: dict) -> tuple[str, dict]:
    ctx = _base(estado, "suscripcion")
    ctx.update(
        {
            "titulo": "Suscripción comunitaria",
            "quebradas": sorted(
                estado.quebradas.values(), key=lambda x: x.nombre
            ),
            "departamentos": estado.departamentos(),
            "suscriptores": [
                {
                    "nombre": s.nombre or "Sin nombre",
                    "telefono": _mascarar_telefono(s.telefono),
                    "telefono_real": s.telefono,
                    "quebrada": s.quebrada,
                    "canal": s.canal,
                    "activo": s.activo,
                }
                for s in estado.suscriptores
            ],
            "mensaje": params.get("mensaje"),
            "error": params.get("error"),
            "sms_modo": "real" if modo_real() else "simulado",
            "sms_proveedor": proveedor_configurado() or "sin proveedor",
        }
    )
    return "suscripcion.html", ctx


# --- Acciones (POST) -------------------------------------------------------


def accion_validar(estado: Estado, params: dict) -> str:
    codigo = params.get("alerta", "")
    a = estado.validar_alerta(codigo, estado.usuario["nombre"])
    if a:
        return f"/alertas?alerta={codigo}&mensaje=Alerta+{codigo}+validada+en+la+simulación"
    return "/alertas"


def accion_notificar_alerta(estado: Estado, params: dict) -> str:
    codigo = str(params.get("alerta", ""))
    alerta = estado.alerta(codigo)
    if alerta is None:
        return f"/alertas?mensaje={quote_plus('Alerta no encontrada.')}"
    if not alerta.activa:
        return f"/alertas?mensaje={quote_plus('La alerta ya está cerrada.')}"
    if alerta.nivel not in ("alto", "critico"):
        return (
            f"/alertas?mensaje="
            f"{quote_plus('Solo se notifican alertas de nivel alto o crítico.')}"
        )
    texto = PLANTILLAS["preventivo"]["texto"]
    nuevas = estado.despachar_alerta(alerta.quebrada, texto, "preventivo")
    enviados = sum(1 for c in nuevas if c.resultado == "enviado")
    fallidos = sum(1 for c in nuevas if c.resultado == "fallido")
    simulados = sum(1 for c in nuevas if c.resultado == "pendiente")
    mensaje = (
        f"Alerta {codigo}: {enviados} SMS enviados, "
        f"{fallidos} fallidos y {simulados} simulados."
    )
    return f"/alertas?alerta={codigo}&mensaje={quote_plus(mensaje)}"


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
    plantilla = params.get("plantilla") or "preventivo"
    texto = PLANTILLAS.get(plantilla, PLANTILLAS["preventivo"])["texto"]
    q = estado.quebrada(codigo)
    destinatarios = q.destinatarios if q else 0
    estado.registrar_comunicacion(
        codigo, destinatarios, canales, texto=texto, plantilla=plantilla
    )
    if modo_real():
        mensaje = (
            f"Se procesó el envío para {len(canales)} canal(es). "
            "Revisa el estado en el historial."
        )
    else:
        mensaje = (
            f"Registro ficticio creado para {len(canales)} canal(es). "
            "No se envió ningún mensaje."
        )
    return (
        f"/notificaciones?quebrada={codigo}"
        f"&mensaje={mensaje.replace(' ', '+')}"
    )


def accion_suscribir(estado: Estado, params: dict) -> str:
    try:
        lat = float(params["lat"]) if params.get("lat") else None
        lon = float(params["lon"]) if params.get("lon") else None
        suscriptor = estado.suscribir(
            str(params.get("nombre", "")),
            str(params.get("telefono", "")),
            str(params.get("quebrada", "")),
            params.get("consentimiento") in ("on", "true", "1", "si", "sí"),
            lat=lat,
            lon=lon,
        )
    except (KeyError, ValueError) as exc:
        return f"/suscripcion?error={quote_plus(str(exc))}"
    mensaje = (
        f"Suscripción registrada para {suscriptor.quebrada}. "
        f"Teléfono {_mascarar_telefono(suscriptor.telefono)}."
    )
    return f"/suscripcion?mensaje={quote_plus(mensaje)}"


def accion_baja(estado: Estado, params: dict) -> str:
    telefono = str(params.get("telefono", ""))
    ok = estado.baja_suscriptor(telefono)
    mensaje = (
        "Suscripción dada de baja."
        if ok
        else "No se encontró una suscripción activa para ese teléfono."
    )
    return f"/suscripcion?mensaje={quote_plus(mensaje)}"


def accion_limpiar_suscriptores(estado: Estado, params: dict) -> str:
    total = estado.limpiar_suscriptores()
    mensaje = f"Historial de suscriptores limpiado ({total})."
    return f"/suscripcion?mensaje={quote_plus(mensaje)}"


def accion_probar_alerta(estado: Estado, params: dict) -> str:
    quebrada = str(params.get("quebrada", ""))
    plantilla = str(params.get("plantilla") or "preventivo")
    if not estado.quebrada(quebrada):
        return f"/suscripcion?error={quote_plus('Quebrada no encontrada.')}"
    texto = PLANTILLAS.get(plantilla, PLANTILLAS["preventivo"])["texto"]
    nuevas = estado.despachar_alerta(quebrada, texto, plantilla)
    enviados = sum(1 for c in nuevas if c.resultado == "enviado")
    fallidos = sum(1 for c in nuevas if c.resultado == "fallido")
    simulados = sum(1 for c in nuevas if c.resultado == "pendiente")
    mensaje = (
        f"Alerta procesada para {len(nuevas)} suscriptor(es): "
        f"{enviados} enviados, {fallidos} fallidos, {simulados} simulados."
    )
    return f"/suscripcion?mensaje={quote_plus(mensaje)}"


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
    departamento = (params.get("departamento") or "").strip()
    provincia = (params.get("provincia") or "").strip()
    distrito = (params.get("distrito") or "").strip()
    problema = estado.validar_ubicacion(departamento, provincia, distrito)
    if problema:
        return f"/configuracion?pestana=umbrales&error={quote_plus(problema)}"
    q = estado.nueva_quebrada(nombre, distrito, provincia, departamento)
    return (
        f"/configuracion?quebrada={q.codigo}"
        f"&mensaje=Quebrada+«{q.nombre}»+registrada+sin+lecturas+asociadas"
    )
