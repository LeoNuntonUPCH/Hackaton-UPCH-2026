"""Estado en memoria de la demostración.

Hace las veces de la base de datos PostgreSQL descrita en la propuesta. Vive
en memoria: al reiniciar el servidor el escenario vuelve a su punto inicial,
que es justo lo que se quiere para una demostración repetible.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from threading import RLock

from . import almacen_postgres, datos
from .datos import (
    AHORA,
    Alerta,
    CambioParametro,
    Comunicacion,
    Quebrada,
)
from .motor import Evaluacion, Umbrales, evaluar, resumen_por_nivel
from .repositorio import Repositorio
from .repositorio_memoria import RepositorioMemoria


class ConflictoIngesta(Exception):
    """La clave de idempotencia ya existe con otro contenido."""


class ConflictoAlerta(Exception):
    """La clave de idempotencia de alerta ya existe con otro contenido."""


class AlertaNoRequerida(Exception):
    """El nivel actual no justifica crear una alerta."""


class Estado:
    """Contenedor único del escenario simulado."""

    def __init__(self, repositorio: Repositorio | None = None) -> None:
        self._lock = RLock()
        self.repo = repositorio or RepositorioMemoria()
        if almacen_postgres.habilitado():
            almacen_postgres.crear_esquema()
        self.reiniciar(persistir=False)
        if almacen_postgres.habilitado():
            if almacen_postgres._vacio():
                almacen_postgres.guardar(self)
            else:
                almacen_postgres.cargar(self)

    # ---- Para Base de datos------

    @property
    def quebradas(self) -> dict[str, Quebrada]:
        return self.repo.quebradas()

    @property
    def alertas(self) -> list[Alerta]:
        return self.repo.alertas()

    @property
    def comunicaciones(self) -> list[Comunicacion]:
        return self.repo.comunicaciones()

    @property
    def historial_parametros(self) -> list[CambioParametro]:
        return self.repo.historial_parametros()

    @property
    def umbrales(self) -> Umbrales:
        return self.repo.umbrales()

    # -- ciclo de vida ----------------------------------------------------

    def reiniciar(self, persistir: bool = True) -> None:
        with self._lock:
            self.repo.reiniciar()
            self.ahora: datetime = AHORA
            self.usuario = datos.USUARIOS["maria.torres@ejemplo.pe"]
            self._contador_alertas = 7
            self.borrador_envio: dict | None = None
            if persistir and almacen_postgres.habilitado():
                almacen_postgres.guardar(self)

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

    def ingerir_lecturas(
        self,
        quebrada: str,
        lecturas: list[float],
        fuente: str,
        idempotency_key: str,
    ) -> dict:
        """Agrega lecturas y devuelve la evaluación resultante.

        No crea alertas: solo informa si el nivel exige una. La clave de
        idempotencia evita duplicar lecturas cuando n8n reintenta un envío.
        """
        with self._lock:
            if not idempotency_key:
                raise ValueError("idempotency_key es obligatorio.")
            if len(idempotency_key) > 128:
                raise ValueError("idempotency_key supera 128 caracteres.")
            if not lecturas:
                raise ValueError("Debe enviar al menos una lectura.")
            if len(lecturas) > 100:
                raise ValueError("No se permiten más de 100 lecturas por envío.")
            if quebrada not in self.quebradas:
                raise KeyError(quebrada)
            for valor in lecturas:
                if not math.isfinite(valor) or valor < 0 or valor > 500:
                    raise ValueError("Cada mm_h debe estar entre 0 y 500.")

            huella = hashlib.sha256(
                json.dumps(
                    {
                        "quebrada": quebrada,
                        "fuente": fuente,
                        "lecturas": lecturas,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()

            existente = self.repo.obtener_ingesta(idempotency_key)
            if existente:
                huella_guardada, resultado = existente
                if huella_guardada != huella:
                    raise ConflictoIngesta(
                        "La clave de idempotencia ya fue usada con otros datos."
                    )
                return {**resultado, "duplicado": True}

            self.repo.agregar_lecturas(quebrada, lecturas)
            ev = self.evaluacion(quebrada)
            resultado = {
                "quebrada": quebrada,
                "fuente": fuente,
                "idempotency_key": idempotency_key,
                "acumulado_mm": ev.acumulado,
                "ventana_horas": self.umbrales.ventana_horas,
                "nivel": ev.nivel,
                "etiqueta": ev.etiqueta,
                "alerta_requerida": ev.nivel in ("alto", "critico"),
                "duplicado": False,
                "lecturas_recibidas": len(lecturas),
            }
            self.repo.guardar_ingesta(idempotency_key, huella, resultado)
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return resultado

    @staticmethod
    def _alerta_dict(alerta: Alerta) -> dict:
        return {
            "codigo": alerta.codigo,
            "quebrada": alerta.quebrada,
            "momento": alerta.momento.isoformat(),
            "nivel": alerta.nivel,
            "estado": alerta.estado,
            "fuente": alerta.fuente,
            "acumulado_mm": alerta.acumulado,
            "nota": alerta.nota,
        }

    def _siguiente_codigo_alerta(self) -> str:
        numeros = []
        for alerta in self.alertas:
            if alerta.codigo.startswith("AL-"):
                try:
                    numeros.append(int(alerta.codigo[3:]))
                except ValueError:
                    continue
        return f"AL-{max(numeros, default=0) + 1:04d}"

    def crear_alerta_si_corresponde(
        self, quebrada: str, fuente: str, idempotency_key: str
    ) -> dict:
        """Crea una alerta si el nivel actual es alto o crítico.

        No crea una segunda alerta activa para la misma quebrada. La clave de
        idempotencia permite que n8n reintente sin duplicar el registro.
        """
        with self._lock:
            if not idempotency_key:
                raise ValueError("idempotency_key es obligatorio.")
            if len(idempotency_key) > 128:
                raise ValueError("idempotency_key supera 128 caracteres.")
            if quebrada not in self.quebradas:
                raise KeyError(quebrada)

            huella = hashlib.sha256(
                json.dumps(
                    {"quebrada": quebrada, "fuente": fuente},
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()

            existente = self.repo.obtener_alerta_por_clave(idempotency_key)
            if existente:
                huella_guardada, resultado = existente
                if huella_guardada != huella:
                    raise ConflictoAlerta(
                        "La clave de idempotencia ya fue usada con otros datos."
                    )
                return {**resultado, "duplicado": True}

            evaluacion = self.evaluacion(quebrada)
            if evaluacion.nivel not in ("alto", "critico"):
                raise AlertaNoRequerida(
                    f"El nivel actual es {evaluacion.etiqueta}; "
                    "no requiere alerta."
                )
            assert evaluacion.acumulado is not None

            for alerta in self.alertas:
                if alerta.quebrada == quebrada and alerta.activa:
                    return {
                        "creada": False,
                        "duplicado": True,
                        "motivo": "alerta_activa",
                        "alerta": self._alerta_dict(alerta),
                    }

            alerta = Alerta(
                codigo=self._siguiente_codigo_alerta(),
                quebrada=quebrada,
                momento=self.ahora,
                nivel=evaluacion.nivel,
                estado="pendiente",
                fuente=fuente,
                acumulado=evaluacion.acumulado,
                nota=(
                    "Creada automáticamente desde n8n en el entorno de "
                    "demostración."
                ),
            )
            resultado = {
                "creada": True,
                "duplicado": False,
                "alerta": self._alerta_dict(alerta),
            }
            self.repo.crear_alerta_con_clave(
                alerta, idempotency_key, huella, resultado
            )
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return resultado

    def validar_alerta(self, codigo: str, responsable: str) -> Alerta | None:
        with self._lock:
            a = self.alerta(codigo)
            if a and a.estado == "pendiente":
                a.estado = "validada"
                a.fuente = "Autoridad · simulación"
                a.nota = f"Validada por {responsable} en el entorno de demostración."
                self.repo.guardar_alerta(a)
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
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
                self.repo.guardar_alerta(a)
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
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
                nuevas.append(c)
            self.repo.agregar_comunicaciones(nuevas)
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return nuevas
    def actualizar_umbrales(self, nuevos: Umbrales, responsable: str) -> list[str]:
        with self._lock:
            problemas = nuevos.validar()
            if problemas:
                return problemas
            anteriores = self.umbrales
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
                            parametro=f"{etiqueta}: {nuevo:g} mm/{nuevos.ventana_horas} h · demo",
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
            self.repo.guardar_umbrales(nuevos, cambios)
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
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
                    self.repo.guardar_alerta(a)
                    cambiadas += 1
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
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

            cambio = CambioParametro(
                momento=self.ahora,
                parametro=f"Alta de quebrada: {nombre} · demo",
                responsable=self.usuario["nombre"],
            )
            self.repo.agregar_quebrada(q, cambio)

            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)

            return q



# Instancia única usada por la aplicación.
ESTADO = Estado()
