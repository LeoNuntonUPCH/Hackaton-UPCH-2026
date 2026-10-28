"""Gráficos en SVG generados en el servidor.

Sin librerías externas: el SVG se arma como texto. Así la demostración se
levanta en cualquier PC con Python y no depende de CDN ni de conexión a
internet, que es una condición práctica para una presentación.
"""

from __future__ import annotations

from datetime import datetime
from html import escape

from .motor import COLORES

# --- Gráfico de precipitación acumulada -----------------------------------


def grafico_acumulado(
    horas: list[datetime],
    valores: list[float],
    umbral_critico: float,
    ventana_horas: int = 6,
    ancho: int = 720,
    alto: int = 240,
    maximo_puntos: int = 6,
) -> str:
    """Línea de acumulado móvil con la línea roja del umbral crítico.

    Se grafican las últimas `maximo_puntos` observaciones: las primeras horas
    de la serie son el periodo de carga de la ventana móvil y no describen
    todavía una acumulación completa.
    """
    if maximo_puntos and len(valores) > maximo_puntos:
        valores = list(valores)[-maximo_puntos:]
        horas = list(horas)[-maximo_puntos:]
    if not valores:
        return (
            '<div class="grafico-vacio">Sin lecturas disponibles para esta '
            "quebrada.</div>"
        )

    m_izq, m_der, m_sup, m_inf = 42, 18, 24, 34
    w = ancho - m_izq - m_der
    h = alto - m_sup - m_inf

    y_max = max(max(valores), umbral_critico) * 1.18
    y_max = max(y_max, 10)

    def px(i: int) -> float:
        if len(valores) == 1:
            return m_izq + w / 2
        return m_izq + w * i / (len(valores) - 1)

    def py(v: float) -> float:
        return m_sup + h - (h * v / y_max)

    partes: list[str] = [
        f'<svg class="grafico" viewBox="0 0 {ancho} {alto}" '
        f'role="img" aria-label="Precipitación acumulada móvil de '
        f'{ventana_horas} horas frente al umbral crítico de '
        f'{umbral_critico:g} milímetros">'
    ]

    # Rejilla horizontal y etiquetas del eje Y.
    paso = _paso_eje(y_max)
    v = 0.0
    while v <= y_max:
        y = py(v)
        partes.append(
            f'<line x1="{m_izq}" y1="{y:.1f}" x2="{ancho - m_der}" y2="{y:.1f}" '
            f'class="g-rejilla"/>'
        )
        partes.append(
            f'<text x="{m_izq - 10}" y="{y + 4:.1f}" class="g-eje" '
            f'text-anchor="end">{v:g}</text>'
        )
        v += paso

    # Línea del umbral crítico.
    y_umbral = py(umbral_critico)
    partes.append(
        f'<line x1="{m_izq}" y1="{y_umbral:.1f}" x2="{ancho - m_der}" '
        f'y2="{y_umbral:.1f}" class="g-umbral"/>'
    )

    # Serie observada.
    puntos = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(valores))
    partes.append(f'<polyline points="{puntos}" class="g-serie"/>')

    for i, val in enumerate(valores):
        partes.append(
            f'<circle cx="{px(i):.1f}" cy="{py(val):.1f}" r="3.4" class="g-punto">'
            f"<title>{val:g} mm/{ventana_horas} h · "
            f"{horas[i].strftime('%H:%M')} PET</title></circle>"
        )

    # Etiqueta del último valor.
    ultimo = valores[-1]
    partes.append(
        f'<text x="{px(len(valores) - 1):.1f}" y="{py(ultimo) - 12:.1f}" '
        f'class="g-valor" text-anchor="middle">{ultimo:g}</text>'
    )

    # Eje X: una etiqueta cada dos puntos para que no se amontonen.
    salto = max(1, len(horas) // 6)
    for i in range(0, len(horas), salto):
        partes.append(
            f'<text x="{px(i):.1f}" y="{alto - 12}" class="g-eje" '
            f'text-anchor="middle">{horas[i].strftime("%H:%M")}</text>'
        )

    partes.append("</svg>")
    return "".join(partes)


def _paso_eje(y_max: float) -> float:
    for paso in (5, 10, 20, 25, 50, 100, 200):
        if y_max / paso <= 5:
            return paso
    return 500


# --- Mapa referencial del Perú --------------------------------------------

# Contorno simplificado del Perú (longitud, latitud). Es una silueta
# referencial de baja resolución: sirve para ubicar marcadores, no para
# delimitar territorio ni rutas.
_CONTORNO = [
    (-80.30, -3.40), (-79.00, -4.90), (-78.20, -3.40), (-77.80, -2.90),
    (-76.00, -4.20), (-75.20, -4.00), (-73.20, -3.80), (-72.40, -2.30),
    (-71.80, -2.20), (-70.05, -2.50), (-70.10, -4.30), (-72.90, -5.10),
    (-73.20, -6.40), (-72.90, -7.60), (-73.80, -7.30), (-74.00, -9.40),
    (-72.20, -10.00), (-70.60, -9.50), (-70.50, -11.00), (-69.60, -10.90),
    (-68.70, -12.50), (-69.30, -13.70), (-68.90, -14.20), (-69.40, -15.20),
    (-69.20, -16.20), (-69.00, -16.50), (-69.60, -17.30), (-70.40, -18.35),
    (-71.30, -17.70), (-72.00, -17.20), (-73.00, -16.50), (-74.50, -15.90),
    (-76.00, -14.60), (-76.30, -13.90), (-77.00, -12.20), (-78.00, -10.00),
    (-78.60, -8.80), (-79.50, -7.90), (-80.80, -6.30), (-81.20, -6.00),
    (-80.90, -5.00), (-81.30, -4.70), (-80.30, -3.40),
]

LON_MIN, LON_MAX = -81.5, -68.5
LAT_MIN, LAT_MAX = -18.6, -2.0

_ETIQUETAS = [
    ("Loreto", -74.0, -4.5), ("Ucayali", -73.5, -9.3), ("Cusco", -72.0, -13.3),
    ("Puno", -70.2, -15.0), ("Arequipa", -72.5, -16.0), ("Lima", -76.9, -12.0),
    ("Áncash", -77.8, -9.4), ("La Libertad", -78.6, -8.0), ("Piura", -80.3, -5.2),
    ("Ayacucho", -74.2, -13.6),
]


def _proyectar(lon: float, lat: float, ancho: float, alto: float,
               borde: float = 14.0) -> tuple[float, float]:
    """Proyección equirectangular que conserva la proporción real.

    Sin esta corrección el país sale estirado a lo ancho: el recuadro es
    apaisado y el territorio es más alto que ancho. Se toma la escala que
    cabe en ambos ejes y se centra el dibujo dentro del recuadro.
    """
    from math import cos, radians

    w = ancho - 2 * borde
    h = alto - 2 * borde

    lat_media = (LAT_MIN + LAT_MAX) / 2
    grados_lon = (LON_MAX - LON_MIN) * cos(radians(lat_media))
    grados_lat = LAT_MAX - LAT_MIN

    escala = min(w / grados_lon, h / grados_lat)
    ancho_util = grados_lon * escala
    alto_util = grados_lat * escala
    dx = borde + (w - ancho_util) / 2
    dy = borde + (h - alto_util) / 2

    x = dx + ancho_util * (lon - LON_MIN) / (LON_MAX - LON_MIN)
    y = dy + alto_util * (LAT_MAX - lat) / (LAT_MAX - LAT_MIN)
    return x, y


def mapa_peru(
    marcadores: list[dict],
    ancho: int = 700,
    alto: int = 520,
    destacado: str | None = None,
    etiquetas: bool = True,
) -> str:
    """Silueta del Perú con marcadores de nivel de riesgo.

    `marcadores` es una lista de dicts con: codigo, nombre, lat, lon, nivel,
    etiqueta, acumulado.
    """
    camino = " ".join(
        ("M" if i == 0 else "L") + "{:.1f} {:.1f}".format(
            *_proyectar(lon, lat, ancho, alto)
        )
        for i, (lon, lat) in enumerate(_CONTORNO)
    ) + " Z"

    partes = [
        f'<svg class="mapa-svg" viewBox="0 0 {ancho} {alto}" '
        f'role="img" aria-label="Mapa referencial del Perú con '
        f'{len(marcadores)} quebradas monitoreadas">',
        '<rect width="100%" height="100%" class="m-fondo"/>',
        f'<text x="26" y="{alto - 92}" class="m-oceano">OCÉANO PACÍFICO</text>',
        f'<path d="{camino}" class="m-pais"/>',
    ]

    if etiquetas:
        for nombre, lon, lat in _ETIQUETAS:
            x, y = _proyectar(lon, lat, ancho, alto)
            partes.append(
                f'<text x="{x:.1f}" y="{y:.1f}" class="m-dep" '
                f'text-anchor="middle">{escape(nombre)}</text>'
            )

    orden = {"bajo": 0, "sin_datos": 0, "moderado": 1, "alto": 2, "critico": 3}
    for m in sorted(marcadores, key=lambda m: orden.get(m["nivel"], 0)):
        x, y = _proyectar(m["lon"], m["lat"], ancho, alto)
        color = COLORES.get(m["nivel"], COLORES["sin_datos"])
        es_destacado = destacado == m["codigo"]
        radio = 11 if es_destacado else 8
        clase = "m-marcador destacado" if es_destacado else "m-marcador"
        titulo = (
            f'{m["nombre"]} · {m["etiqueta"]} · '
            f'{m.get("acumulado_texto", "sin dato")}'
        )
        partes.append(
            f'<g class="{clase}">'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radio + 5}" '
            f'fill="{color}" opacity="0.16"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radio}" fill="{color}" '
            f'stroke="#FFFFFF" stroke-width="2"/>'
            f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" '
            f'class="m-glifo">{escape(m.get("glifo", "•"))}</text>'
            f"<title>{escape(titulo)}</title>"
            f"</g>"
        )

    partes.append("</svg>")
    return "".join(partes)
