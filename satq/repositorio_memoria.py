from __future__ import annotations

from . import datos
from .datos import Alerta, CambioParametro, Comunicacion, Quebrada
from .motor import Umbrales


class RepositorioMemoria:
    def __init__ (self) -> None:
        self.reiniciar()

    def reiniciar(self) -> None:
        self._quebradas = datos.construir_quebradas()
        self._alertas = datos.construir_alertas()
        self._comunicaciones = datos.construir_comunicaciones()
        self._historial = datos.construir_historial_parametros()
        self._umbrales = datos.umbrales_iniciales()
        self._ingestas: dict[str, tuple[str, dict]] = {}
        self._alertas_por_clave: dict[str, tuple[str, dict]] = {}

    def quebradas(self) -> dict[str,Quebrada]:
        return self._quebradas

    def alertas(self) -> list[Alerta]:
        return self._alertas

    def comunicaciones(self) -> list[Comunicacion]:
        return self._comunicaciones

    def historial_parametros(self) -> list[CambioParametro]:
        return self._historial

    def umbrales(self) -> Umbrales:
        return self._umbrales

    def agregar_lecturas(self, codigo: str, lecturas: list[float]) -> None:
        self._quebradas[codigo].lecturas.extend(lecturas)

    def obtener_ingesta(self, clave: str) -> tuple[str, dict] | None:
        return self._ingestas.get(clave)

    def guardar_ingesta(
        self, clave: str, huella: str, resultado: dict
    ) -> None:
        self._ingestas[clave] = (huella, dict(resultado))

    def guardar_alerta(self,alerta:Alerta) -> None:
        for i,actual in enumerate(self._alertas):
            if actual.codigo == alerta.codigo:
                self._alertas[i] = alerta
                return
        self._alertas.append(alerta)

    def obtener_alerta_por_clave(self, clave: str) -> tuple[str, dict] | None:
        return self._alertas_por_clave.get(clave)

    def crear_alerta_con_clave(
        self, alerta: Alerta, clave: str, huella: str, resultado: dict
    ) -> None:
        self._alertas.append(alerta)
        self._alertas_por_clave[clave] = (huella, dict(resultado))

    def guardar_umbrales(
        self, umbrales : Umbrales, cambios: list[CambioParametro]
    ) -> None:
        self._umbrales = umbrales
        for cambio in reversed(cambios):
            self._historial.insert(0,cambio)

    def agregar_comunicaciones(self,nuevas: list[Comunicacion]) -> None:
        for comunicacion in nuevas:
            self._comunicaciones.insert(0,comunicacion)

    def agregar_quebrada(self, quebrada: Quebrada, cambio: CambioParametro) -> None:
        self._quebradas[quebrada.codigo] = quebrada
        self._historial.insert(0,cambio)







