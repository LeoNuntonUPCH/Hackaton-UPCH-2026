"""Motor de clasificación de riesgo del SATQ Digital.

Regla única del sistema: dada la precipitación acumulada en una ventana móvil
(por defecto 6 horas) y un conjunto de umbrales configurables, devolver el
nivel de riesgo. Es la pieza que la propuesta describe como "el software
calculará de manera estandarizada los umbrales de riesgo".

Todos los valores son de demostración. El motor no predice: describe el
registro observado frente al umbral configurado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

# Orden de severidad, de menor a mayor.
NIVELES = ("bajo", "moderado", "alto", "critico")

ETIQUETAS = {
    "bajo": "Bajo",
    "moderado": "Moderado",
    "alto": "Alto",
    "critico": "Crítico",
}

# Glifo usado en el Figma para cada nivel (acompaña al color, para que el
# nivel no dependa solo del color y siga siendo legible en impresión).
GLIFOS = {
    "bajo": "●",
    "moderado": "◇",
    "alto": "△",
    "critico": "⚠",
}

COLORES = {
    "bajo": "#12A594",
    "moderado": "#E8A317",
    "alto": "#F07B29",
    "critico": "#D92D20",
    "sin_datos": "#94A3B8",
}


@dataclass
class Umbrales:
    """Límites inferiores de cada nivel, en mm por ventana de acumulación."""

    bajo: float = 0.0
    moderado: float = 20.0
    alto: float = 30.0
    critico: float = 40.0
    ventana_horas: int = 6
    unidad: str = "mm / 6 h"

    def como_lista(self) -> list[dict]:
        """Filas listas para la tabla de 'Umbrales por nivel de riesgo'."""
        limites = [
            ("bajo", self.bajo, self.moderado),
            ("moderado", self.moderado, self.alto),
            ("alto", self.alto, self.critico),
            ("critico", self.critico, None),
        ]
        filas = []
        for nivel, desde, hasta in limites:
            if hasta is None:
                rango = f"≥{_num(desde)} mm/{self.ventana_horas} h"
            else:
                rango = f"{_num(desde)} a <{_num(hasta)} mm/{self.ventana_horas} h"
            filas.append(
                {
                    "nivel": nivel,
                    "etiqueta": ETIQUETAS[nivel],
                    "glifo": GLIFOS[nivel],
                    "color": COLORES[nivel],
                    "rango": rango,
                    "limite_inferior": desde,
                    "limite_texto": f"{_num(desde)} mm/{self.ventana_horas} h",
                }
            )
        return filas

    def validar(self) -> list[str]:
        """Devuelve la lista de problemas encontrados (vacía si todo es válido)."""
        problemas: list[str] = []
        if self.bajo != 0:
            problemas.append("El límite inferior del nivel Bajo debe ser 0.")
        if not (self.bajo < self.moderado < self.alto < self.critico):
            problemas.append(
                "Los umbrales deben ser estrictamente crecientes: "
                "Bajo < Moderado < Alto < Crítico."
            )
        if self.critico > 500:
            problemas.append("El umbral crítico supera el rango admitido (500 mm).")
        if self.ventana_horas not in (1, 3, 6, 12, 24):
            problemas.append("La ventana de acumulación debe ser 1, 3, 6, 12 o 24 horas.")
        return problemas


def _num(valor: float) -> str:
    """Formatea sin decimales innecesarios: 40.0 -> '40', 20.5 -> '20.5'."""
    return f"{valor:g}"


def clasificar(acumulado_mm: float | None, umbrales: Umbrales) -> str:
    """Devuelve el nivel de riesgo para un acumulado dado.

    Un acumulado desconocido no se clasifica como 'bajo': se marca como
    'sin_datos', porque ausencia de dato no es ausencia de riesgo.
    """
    if acumulado_mm is None:
        return "sin_datos"
    if acumulado_mm >= umbrales.critico:
        return "critico"
    if acumulado_mm >= umbrales.alto:
        return "alto"
    if acumulado_mm >= umbrales.moderado:
        return "moderado"
    return "bajo"


def acumulado_movil(
    lecturas: Sequence[float], ventana_horas: int, paso_horas: int = 1
) -> list[float]:
    """Acumulado móvil sobre una serie de lecturas horarias de lluvia (mm/h)."""
    pasos = max(1, int(ventana_horas / paso_horas))
    salida: list[float] = []
    for i in range(len(lecturas)):
        trozo = lecturas[max(0, i - pasos + 1) : i + 1]
        salida.append(round(sum(trozo), 1))
    return salida


@dataclass
class Evaluacion:
    """Resultado de evaluar una quebrada contra los umbrales vigentes."""

    nivel: str
    acumulado: float | None
    umbral_critico: float
    ventana_horas: int
    excedente: float | None = None
    niveles_superados: list[str] = field(default_factory=list)

    @property
    def etiqueta(self) -> str:
        return ETIQUETAS.get(self.nivel, "Sin datos")

    @property
    def glifo(self) -> str:
        return GLIFOS.get(self.nivel, "○")

    @property
    def color(self) -> str:
        return COLORES.get(self.nivel, COLORES["sin_datos"])

    @property
    def supera_critico(self) -> bool:
        return self.nivel == "critico"

    @property
    def texto_excedente(self) -> str:
        if self.excedente is None:
            return "Sin dato de acumulación para esta ventana."
        if self.excedente >= 0:
            return f"Superación observada: +{_num(self.excedente)} mm/{self.ventana_horas} h"
        return (
            f"Margen al umbral crítico: {_num(abs(self.excedente))} "
            f"mm/{self.ventana_horas} h"
        )


def evaluar(acumulado_mm: float | None, umbrales: Umbrales) -> Evaluacion:
    """Evalúa un acumulado y describe su posición frente a los umbrales."""
    nivel = clasificar(acumulado_mm, umbrales)
    excedente = None
    superados: list[str] = []
    if acumulado_mm is not None:
        excedente = round(acumulado_mm - umbrales.critico, 1)
        for n in NIVELES:
            limite = getattr(umbrales, n)
            if n != "bajo" and acumulado_mm >= limite:
                superados.append(n)
    return Evaluacion(
        nivel=nivel,
        acumulado=acumulado_mm,
        umbral_critico=umbrales.critico,
        ventana_horas=umbrales.ventana_horas,
        excedente=excedente,
        niveles_superados=superados,
    )


def resumen_por_nivel(evaluaciones: Iterable[Evaluacion]) -> dict[str, int]:
    """Cuenta cuántas quebradas hay en cada nivel."""
    conteo = {n: 0 for n in NIVELES}
    conteo["sin_datos"] = 0
    for ev in evaluaciones:
        conteo[ev.nivel] = conteo.get(ev.nivel, 0) + 1
    return conteo
