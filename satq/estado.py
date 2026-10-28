"""Estado en memoria de la demostración.

Hace las veces de la base de datos PostgreSQL descrita en la propuesta. Vive
en memoria: al reiniciar el servidor el escenario vuelve a su punto inicial,
que es justo lo que se quiere para una demostración repetible.
"""

from __future__ import annotations

from datetime import datetime
from threading import RLock

from . import datos
from .datos import (
    AHORA,
    Alerta,
    CambioParametro,
    Comunicacion,
    Quebrada,
)
from .motor import Evaluacion, Umbrales, evaluar, resumen_por_nivel


class Estado:
    """Contenedor único del escenario simulado."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reiniciar()

    # -- ciclo de vida ----------------------------------------------------

    def reiniciar(self) -> None:
        with self._lock:
            self.quebradas: dict[str, Quebrada] = datos.construir_quebradas()
            self.alertas: list[Alerta] = datos.construir_alertas()
            self.comunicaciones: list[Comunicacion] = datos.construir_comunicaciones()
            self.historial_parametros: list[CambioParametro] = (
                datos.construir_historial_parametros()
            )
            self.umbrales: Umbrales = datos.umbrales_iniciales()
            self.ahora: datetime = AHORA
            self.usuario = datos.USUARIOS["maria.torres@ejemplo.pe"]
            self._contador_alertas = 7
            self.borrador_envio: dict | None = None

    # -- lectura ----------------------------------------------------------

    def quebrada(self, codigo: str) -> Quebrada | None:
        return self.quebradas.get(codigo)

    def evaluacion(self, codigo: str) -> Evaluacion:
        q = self.quebradas[codigo]
        return evaluar(q.acumulado_actual(self.umbrales.ventana_horas), self.umbrales)

    def evaluaciones(self) -> dict[str, Evaluacion]:
        return {cod: self.evaluacion(cod) for cod in self.quebradas}

    def resumen(self) -> dict[str, int]:
        return resumen_por_nivel(self.evaluaciones().values())

    def alertas_activas(self) -> list[Alerta]:
        return [a for a in self.alertas if a.activa]

    def conteo_estados(self) -> dict[str, int]:
        conteo = {"activas": 0, "pendiente": 0, "validada": 0, "enviada": 0,
                  "cerrada": 0}
        for a in self.alertas:
            conteo[a.estado] = conteo.get(a.estado, 0) + 1
            if a.activa:
                conteo["activas"] += 1
        return conteo

    def alerta(self, codigo: str) -> Alerta | None:
        for a in self.alertas:
            if a.codigo == codigo:
                return a
        return None

    def localidades_en_riesgo(self) -> int:
        """Quebradas en nivel moderado o superior."""
        return sum(
            1
            for ev in self.evaluaciones().values()
            if ev.nivel in ("moderado", "alto", "critico")
        )

    def departamentos(self) -> list[str]:
        return sorted({q.departamento for q in self.quebradas.values()})

    def provincias(self, departamento: str | None = None) -> list[str]:
        return sorted(
            {
                q.provincia
                for q in self.quebradas.values()
                if not departamento or q.departamento == departamento
            }
        )

    def distritos(self, provincia: str | None = None) -> list[str]:
        return sorted(
            {
                q.distrito
                for q in self.quebradas.values()
                if not provincia or q.provincia == provincia
            }
        )

    def filtrar_quebradas(
        self,
        departamento: str | None = None,
        provincia: str | None = None,
        distrito: str | None = None,
    ) -> list[Quebrada]:
        salida = []
        for q in self.quebradas.values():
            if departamento and q.departamento != departamento:
                continue
            if provincia and q.provincia != provincia:
                continue
            if distrito and q.distrito != distrito:
                continue
            salida.append(q)
        return sorted(salida, key=lambda q: q.nombre)

    def filtrar_alertas(
        self,
        nivel: str | None = None,
        departamento: str | None = None,
        estado: str | None = None,
    ) -> list[Alerta]:
        salida = []
        for a in self.alertas:
            q = self.quebradas.get(a.quebrada)
            if nivel and a.nivel != nivel:
                continue
            if departamento and (not q or q.departamento != departamento):
                continue
            if estado == "activas" and not a.activa:
                continue
            if estado and estado not in ("activas", "todas") and a.estado != estado:
                continue
            salida.append(a)
        return sorted(salida, key=lambda a: a.momento, reverse=True)

    # -- escritura --------------------------------------------------------

    def validar_alerta(self, codigo: str, responsable: str) -> Alerta | None:
        with self._lock:
            a = self.alerta(codigo)
            if a and a.estado == "pendiente":
                a.estado = "validada"
                a.fuente = "Autoridad · simulación"
                a.nota = f"Validada por {responsable} en el entorno de demostración."
            return a

    def cambiar_estado_alerta(self, codigo: str, nuevo: str,
                              responsable: str) -> Alerta | None:
        with self._lock:
            a = self.alerta(codigo)
            if a and nuevo in datos.ESTADOS:
                a.estado = nuevo
                a.nota = (
                    f"Estado cambiado a «{datos.ESTADOS[nuevo]}» por {responsable} "
                    "en el entorno de demostración."
                )
            return a

    def registrar_comunicacion(
        self, quebrada: str, destinatarios: int, canales: list[str]
    ) -> list[Comunicacion]:
        with self._lock:
            nuevas = []
            for canal in canales:
                c = Comunicacion(
                    momento=self.ahora,
                    quebrada=quebrada,
                    destinatarios=destinatarios,
                    canal=canal,
                    resultado="pendiente",
                    entrega_real="No disponible",
                )
                self.comunicaciones.insert(0, c)
                nuevas.append(c)
            return nuevas

    def actualizar_umbrales(
        self, nuevos: Umbrales, responsable: str
    ) -> list[str]:
        """Aplica umbrales nuevos. Devuelve los problemas si no son válidos."""
        with self._lock:
            problemas = nuevos.validar()
            if problemas:
                return problemas
            anteriores = self.umbrales
            self.umbrales = nuevos
            cambios = []
            for campo, etiqueta in (
                ("moderado", "Moderado"),
                ("alto", "Alto"),
                ("critico", "Crítico"),
            ):
                viejo = getattr(anteriores, campo)
                nuevo = getattr(nuevos, campo)
                if viejo != nuevo:
                    cambios.append(
                        CambioParametro(
                            momento=self.ahora,
                            parametro=f"{etiqueta}: {nuevo:g} mm/"
                                      f"{nuevos.ventana_horas} h · demo",
                            responsable=responsable,
                            critico=(campo == "critico"),
                        )
                    )
            if anteriores.ventana_horas != nuevos.ventana_horas:
                cambios.append(
                    CambioParametro(
                        momento=self.ahora,
                        parametro=f"Ventana: {nuevos.ventana_horas} h · demo",
                        responsable=responsable,
                    )
                )
            for c in reversed(cambios):
                self.historial_parametros.insert(0, c)
            return []

    def recalcular_alertas(self) -> int:
        """Re-evalúa las alertas abiertas con los umbrales vigentes.

        Devuelve cuántas cambiaron de nivel. Es el gesto que demuestra que el
        motor, y no una tabla fija, decide el nivel de riesgo.
        """
        with self._lock:
            cambiadas = 0
            for a in self.alertas:
                if not a.activa:
                    continue
                nuevo = evaluar(a.acumulado, self.umbrales).nivel
                if nuevo != a.nivel:
                    a.nivel = nuevo
                    cambiadas += 1
            return cambiadas

    def nueva_quebrada(
        self, nombre: str, distrito: str, provincia: str, departamento: str
    ) -> Quebrada:
        with self._lock:
            codigo = nombre.lower().replace(" ", "-")[:40] or "quebrada"
            sufijo = 1
            base = codigo
            while codigo in self.quebradas:
                sufijo += 1
                codigo = f"{base}-{sufijo}"
            q = Quebrada(
                codigo=codigo,
                nombre=nombre,
                distrito=distrito,
                provincia=provincia,
                departamento=departamento,
                lat=-12.0,
                lon=-77.0,
                lecturas=[],
                destinatarios=0,
            )
            self.quebradas[codigo] = q
            self.historial_parametros.insert(
                0,
                CambioParametro(
                    momento=self.ahora,
                    parametro=f"Alta de quebrada: {nombre} · demo",
                    responsable=self.usuario["nombre"],
                ),
            )
            return q


# Instancia única usada por la aplicación.
ESTADO = Estado()
