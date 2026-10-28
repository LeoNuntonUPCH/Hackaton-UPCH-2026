"""Datos simulados del SATQ Digital.

Nada de lo que hay aquí proviene de SENAMHI, INAIGEM ni de ninguna fuente
oficial. Son series sintéticas, deterministas (semilla fija) y reproducibles,
pensadas para que la demostración muestre siempre el mismo escenario.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .motor import Umbrales, acumulado_movil

# Momento congelado de la demostración, igual al del diseño.
AHORA = datetime(2026, 10, 26, 10, 35)
ZONA = "PET"


@dataclass
class Quebrada:
    codigo: str
    nombre: str
    distrito: str
    provincia: str
    departamento: str
    lat: float
    lon: float
    lecturas: list[float] = field(default_factory=list)  # mm/h, última = más reciente
    destinatarios: int = 0
    grupo: str = "Comité local de prevención"
    destacada: bool = False

    @property
    def ubicacion_corta(self) -> str:
        return f"{self.nombre} · {self.departamento}"

    @property
    def ubicacion_larga(self) -> str:
        return (
            f"Distrito {self.distrito} · Provincia {self.provincia} "
            f"· Departamento {self.departamento}"
        )

    def serie_acumulada(self, ventana_horas: int) -> list[float]:
        return acumulado_movil(self.lecturas, ventana_horas)

    def acumulado_actual(self, ventana_horas: int) -> float | None:
        if not self.lecturas:
            return None
        return self.serie_acumulada(ventana_horas)[-1]

    def horas(self) -> list[datetime]:
        n = len(self.lecturas)
        return [AHORA - timedelta(hours=n - 1 - i) for i in range(n)]


@dataclass
class Alerta:
    codigo: str
    quebrada: str          # código de quebrada
    momento: datetime
    nivel: str             # nivel registrado al momento de la detección
    estado: str            # pendiente | validada | enviada | cerrada
    fuente: str
    acumulado: float
    nota: str = ""

    @property
    def activa(self) -> bool:
        return self.estado != "cerrada"


@dataclass
class Comunicacion:
    momento: datetime
    quebrada: str
    destinatarios: int
    canal: str             # SMS | WhatsApp
    resultado: str         # enviado | pendiente | fallido
    entrega_real: str = "No disponible"


@dataclass
class CambioParametro:
    momento: datetime
    parametro: str
    responsable: str
    critico: bool = False


ESTADOS = {
    "pendiente": "Pendiente de revisión",
    "validada": "Validada",
    "enviada": "Enviada",
    "cerrada": "Cerrada",
}

RESULTADOS = {
    "enviado": "Enviado · simulación",
    "pendiente": "Pendiente · simulación",
    "fallido": "Fallido · simulación",
}

PLANTILLAS = {
    "preventivo": {
        "nombre": "Aviso preventivo · Riesgo elevado",
        "texto": (
            "ALERTA SATQ: Se ha identificado un nivel de riesgo elevado en la zona "
            "seleccionada. Sigue las indicaciones de las autoridades locales, aléjate "
            "de la quebrada y dirígete a una zona segura verificada"
        ),
    },
    "seguimiento": {
        "nombre": "Aviso de seguimiento · Lluvia en aumento",
        "texto": (
            "SATQ: La lluvia acumulada en tu zona sigue en aumento. Mantente atento a "
            "las indicaciones de tu municipalidad y evita acercarte al cauce"
        ),
    },
    "cierre": {
        "nombre": "Cierre de episodio · Fin de aviso",
        "texto": (
            "SATQ: El episodio de lluvia registrado en tu zona ha disminuido. Consulta "
            "a tu municipalidad antes de retomar actividades cerca de la quebrada"
        ),
    },
}

USUARIOS = {
    "maria.torres@ejemplo.pe": {
        "nombre": "María Torres",
        "rol": "Autoridad regional",
        "iniciales": "MT",
        "permisos": "autoridad",
    },
    "diego.salazar@ejemplo.pe": {
        "nombre": "Diego Salazar",
        "rol": "Personal técnico",
        "iniciales": "DS",
        "permisos": "tecnico",
    },
}


# --- Construcción de las quebradas de demostración -------------------------

_BASE = [
    # (codigo, nombre, distrito, provincia, departamento, lat, lon, pico mm/6h, destinatarios)
    ("huaycoloro", "Huaycoloro", "Lurigancho-Chosica", "Lima", "Lima",
     -11.95, -76.95, 42.0, 12),
    ("chaclacayo", "Chaclacayo", "Chaclacayo", "Lima", "Lima",
     -11.98, -76.77, 34.0, 12),
    ("el-porvenir", "El Porvenir", "El Porvenir", "Trujillo", "La Libertad",
     -8.08, -79.02, 31.0, 8),
    ("castilla", "Castilla", "Castilla", "Piura", "Piura",
     -5.21, -80.62, 24.0, 10),
]

_SECUNDARIAS = [
    ("quirio", "Quirio", "Lurigancho-Chosica", "Lima", "Lima", -11.93, -76.70, 18.0),
    ("pedregal", "Pedregal", "Lurigancho-Chosica", "Lima", "Lima", -11.94, -76.72, 15.0),
    ("cashahuacra", "Cashahuacra", "Santa Eulalia", "Huarochirí", "Lima", -11.89, -76.66, 21.0),
    ("corrales", "Corrales", "Ate", "Lima", "Lima", -12.02, -76.90, 12.0),
    ("rayos-sol", "Rayos de Sol", "Chosica", "Lima", "Lima", -11.92, -76.69, 9.0),
    ("huampani", "Huampaní", "Chaclacayo", "Lima", "Lima", -11.97, -76.80, 17.0),
    ("mariscal", "Mariscal Castilla", "Chosica", "Lima", "Lima", -11.93, -76.71, 7.0),
    ("san-antonio", "San Antonio", "Jicamarca", "Huarochirí", "Lima", -11.90, -76.93, 23.0),
    ("yanacoto", "Yanacoto", "Lurigancho-Chosica", "Lima", "Lima", -11.95, -76.73, 11.0),
    ("carosio", "Carosio", "Chaclacayo", "Lima", "Lima", -11.98, -76.78, 6.0),
    ("huaycan", "Huaycán", "Ate", "Lima", "Lima", -12.01, -76.81, 19.0),
    ("santa-maria", "Santa María", "Huachipa", "Lima", "Lima", -11.99, -76.91, 13.0),
    ("la-cantuta", "La Cantuta", "Chosica", "Lima", "Lima", -11.91, -76.68, 8.0),
    ("virgen-rosario", "Virgen del Rosario", "El Porvenir", "Trujillo", "La Libertad",
     -8.06, -79.01, 16.0),
    ("san-idelfonso", "San Idelfonso", "Trujillo", "Trujillo", "La Libertad",
     -8.05, -78.98, 26.0),
    ("leon-dormido", "León Dormido", "Laredo", "Trujillo", "La Libertad",
     -8.09, -78.96, 14.0),
    ("cura-mori", "Cura Mori", "Cura Mori", "Piura", "Piura", -5.30, -80.65, 19.0),
    ("tacala", "Tacalá", "Castilla", "Piura", "Piura", -5.19, -80.60, 10.0),
    ("chulucanas", "Chulucanas", "Chulucanas", "Morropón", "Piura", -5.09, -80.16, 22.0),
    ("mollepata", "Mollepata", "Carmen Alto", "Huamanga", "Ayacucho", -13.17, -74.23, 18.0),
]


def _serie(pico: float, semilla: int, puntos: int = 12) -> list[float]:
    """Genera lecturas horarias (mm/h) para un episodio de lluvia simulado.

    El episodio empieza seis horas antes del momento de la demostración: las
    primeras lecturas son cero, de modo que el acumulado móvil de 6 h sube
    desde casi nada hasta `pico`. Así la curva muestra una evolución y no una
    recta ya saturada.

    La suma de las últimas seis lecturas es exactamente `pico`, para que el
    nivel de riesgo mostrado sea reproducible en cada ejecución.
    """
    rnd = random.Random(semilla)

    # Reparto del episodio entre las últimas seis horas. Suma = 1.
    reparto = [0.095, 0.190, 0.190, 0.190, 0.167, 0.168]
    # Pequeña variación determinista entre quebradas, sin alterar el total.
    sacudida = [rnd.uniform(-0.02, 0.02) for _ in reparto]
    sacudida[-1] -= sum(sacudida)
    reparto = [max(0.01, r + s) for r, s in zip(reparto, sacudida)]
    total = sum(reparto)
    reparto = [r / total for r in reparto]

    lecturas = [0.0] * max(0, puntos - 6)
    lecturas += [round(pico * r, 2) for r in reparto]

    # Corrección del redondeo para que el acumulado final sea exacto.
    diferencia = round(pico - sum(lecturas[-6:]), 2)
    lecturas[-1] = round(lecturas[-1] + diferencia, 2)
    return lecturas


def construir_quebradas() -> dict[str, Quebrada]:
    quebradas: dict[str, Quebrada] = {}
    for i, (cod, nom, dis, pro, dep, lat, lon, pico, dest) in enumerate(_BASE):
        quebradas[cod] = Quebrada(
            codigo=cod, nombre=nom, distrito=dis, provincia=pro, departamento=dep,
            lat=lat, lon=lon, lecturas=_serie(pico, 100 + i), destinatarios=dest,
            destacada=True,
        )
    for i, (cod, nom, dis, pro, dep, lat, lon, pico) in enumerate(_SECUNDARIAS):
        quebradas[cod] = Quebrada(
            codigo=cod, nombre=nom, distrito=dis, provincia=pro, departamento=dep,
            lat=lat, lon=lon, lecturas=_serie(pico, 200 + i), destinatarios=6,
        )
    return quebradas


def _h(hora: int, minuto: int, dia: int = 26) -> datetime:
    return datetime(2026, 10, dia, hora, minuto)


def construir_alertas() -> list[Alerta]:
    """Las siete alertas del escenario de demostración."""
    return [
        Alerta("AL-0007", "huaycoloro", _h(10, 35), "critico", "pendiente",
               "Automática · demo", 42.0,
               "Detección automática registrada. Pendiente de revisión."),
        Alerta("AL-0006", "chaclacayo", _h(10, 20), "alto", "validada",
               "Autoridad · simulación", 34.0,
               "Revisada por autoridad regional en el entorno de demostración."),
        Alerta("AL-0005", "el-porvenir", _h(10, 5), "alto", "enviada",
               "Autoridad · simulación", 31.0,
               "Comunicación preparada y registrada como enviada en la simulación."),
        Alerta("AL-0004", "castilla", _h(9, 50), "moderado", "pendiente",
               "Automática · demo", 24.0,
               "Detección automática registrada. Pendiente de revisión."),
        Alerta("AL-0003", "chaclacayo", _h(9, 40), "moderado", "validada",
               "Autoridad · simulación", 22.0,
               "Revisada por autoridad regional en el entorno de demostración."),
        Alerta("AL-0002", "castilla", _h(9, 25), "moderado", "pendiente",
               "Automática · demo", 21.0,
               "Detección automática registrada. Pendiente de revisión."),
        Alerta("AL-0001", "huaycoloro", _h(16, 10, dia=25), "moderado", "cerrada",
               "Autoridad · simulación", 23.0,
               "Episodio cerrado por la autoridad en el entorno de demostración."),
    ]


def construir_comunicaciones() -> list[Comunicacion]:
    return [
        Comunicacion(_h(10, 20), "chaclacayo", 12, "SMS", "enviado"),
        Comunicacion(_h(10, 10), "el-porvenir", 8, "WhatsApp", "pendiente"),
        Comunicacion(_h(9, 50), "castilla", 10, "SMS", "fallido"),
    ]


def construir_historial_parametros() -> list[CambioParametro]:
    return [
        CambioParametro(_h(9, 0), "Crítico: 40 mm/6 h · demo", "Diego Salazar",
                        critico=True),
        CambioParametro(_h(16, 30, dia=25), "Ventana: 6 h · demo", "Diego Salazar"),
    ]


def umbrales_iniciales() -> Umbrales:
    return Umbrales(bajo=0.0, moderado=20.0, alto=30.0, critico=40.0, ventana_horas=6)


# Historial de alertas mostrado en el detalle de quebrada (por quebrada).
def historial_quebrada(codigo: str, alertas: list[Alerta]) -> list[Alerta]:
    return [a for a in alertas if a.quebrada == codigo]


CONECTORES = [
    {
        "nombre": "SENAMHI",
        "estado": "Integración propuesta · No implementada",
        "detalle": "Última sincronización: no disponible",
        "conectado": False,
    },
    {
        "nombre": "INAIGEM",
        "estado": "Integración propuesta · No implementada",
        "detalle": "Última sincronización: no disponible",
        "conectado": False,
    },
]

CANALES = [
    {"nombre": "WhatsApp", "conectado": False},
    {"nombre": "SMS", "conectado": False},
]

CAPAS_MAPA = [
    {"nombre": "Límites departamentales", "detalle": "Visible · referencial",
     "activa": True, "bloqueada": False},
    {"nombre": "Localidades expuestas", "detalle": "No verificado",
     "activa": False, "bloqueada": True},
    {"nombre": "Vías afectadas", "detalle": "Sin datos disponibles",
     "activa": False, "bloqueada": True},
    {"nombre": "Puntos de evacuación", "detalle": "Sin información verificada",
     "activa": False, "bloqueada": True},
    {"nombre": "Zonas seguras", "detalle": "Sin información verificada",
     "activa": False, "bloqueada": True},
]

RECOMENDACIONES = [
    {
        "titulo": "Aléjate del cauce",
        "texto": "Evita permanecer en la quebrada o en sus márgenes.",
    },
    {
        "titulo": "Sigue indicaciones oficiales",
        "texto": "Consulta a las autoridades locales antes de desplazarte.",
    },
    {
        "titulo": "No cruces flujos de agua",
        "texto": "Evita puentes o vías si observas material arrastrado.",
    },
]
