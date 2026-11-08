"""Estado en memoria de la demostración.

Hace las veces de la base de datos PostgreSQL descrita en la propuesta. Vive
en memoria: al reiniciar el servidor el escenario vuelve a su punto inicial,
que es justo lo que se quiere para una demostración repetible.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import secrets
from datetime import datetime, timedelta
from threading import RLock

from mensajeria import ResultadoEnvio, maximo_envios, modo_real, obtener_canal

from . import almacen_postgres, datos
from .datos import (
    AHORA,
    Alerta,
    CambioParametro,
    Comunicacion,
    Quebrada,
    Suscriptor,
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
        self._envios_realizados = {
            c.clave_idempotencia
            for c in self.comunicaciones
            if c.clave_idempotencia and c.resultado == "enviado"
        }

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

    @property
    def suscriptores(self) -> list[Suscriptor]:
        return self.repo.suscriptores()

    # -- ciclo de vida ----------------------------------------------------

    def reiniciar(self, persistir: bool = True) -> None:
        with self._lock:
            self.repo.reiniciar()
            self.ahora: datetime = AHORA
            self.usuario = datos.USUARIOS["maria.torres@ejemplo.pe"]
            self._contador_alertas = 7
            self.borrador_envio: dict | None = None
            self._envios_realizados = set()
            self._ultimo_codigo: dict[str, datetime] = {}
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

    def distritos(
        self, provincia: str | None = None, departamento: str | None = None
    ) -> list[str]:
        return sorted(
            {
                q.distrito
                for q in self.quebradas.values()
                if (not provincia or q.provincia == provincia)
                and (not departamento or q.departamento == departamento)
            }
        )

    def jerarquia(self) -> dict[str, list]:
        """Árbol departamento → provincia → distrito → quebrada.

        Alimenta los desplegables dependientes: cada opción lleva sus padres,
        así el navegador puede ocultar las que no corresponden.
        """
        provincias = sorted({(q.departamento, q.provincia) for q in self.quebradas.values()})
        distritos = sorted(
            {(q.departamento, q.provincia, q.distrito) for q in self.quebradas.values()}
        )
        quebradas = sorted(self.quebradas.values(), key=lambda q: q.nombre)
        return {
            "departamentos": self.departamentos(),
            "provincias": provincias,
            "distritos": distritos,
            "quebradas": quebradas,
        }

    def normalizar_ubicacion(
        self,
        departamento: str = "",
        provincia: str = "",
        distrito: str = "",
        quebrada: str = "",
    ) -> dict[str, str]:
        """Descarta los niveles que no pertenecen a su padre.

        Si llega «Piura / Lima» (una provincia que quedó de un filtro anterior),
        la provincia se descarta en vez de devolver cero resultados sin aviso.
        """
        if departamento not in self.departamentos():
            departamento = ""
        if provincia and provincia not in self.provincias(departamento or None):
            provincia = ""
        if distrito and distrito not in self.distritos(
            provincia or None, departamento or None
        ):
            distrito = ""
        if quebrada and quebrada not in {
            q.codigo
            for q in self.filtrar_quebradas(departamento, provincia, distrito)
        }:
            quebrada = ""
        return {
            "departamento": departamento,
            "provincia": provincia,
            "distrito": distrito,
            "quebrada": quebrada,
        }

    def validar_ubicacion(
        self, departamento: str, provincia: str, distrito: str
    ) -> str | None:
        """Comprueba que una ubicación nueva no contradiga la jerarquía existente.

        Devuelve el motivo del rechazo o None si es coherente. Solo se valida
        provincia → departamento: los nombres de distrito sí se repiten dentro
        de un mismo departamento (p. ej. San Antonio en Cañete y en Huarochirí),
        así que rechazarlos daría falsos errores. La validación completa exige
        un catálogo de ubigeo que el prototipo no incluye.
        """
        if not (departamento and provincia and distrito):
            return "Indica departamento, provincia y distrito."
        for q in self.quebradas.values():
            if q.provincia == provincia and q.departamento != departamento:
                return (
                    f"La provincia {provincia} ya está registrada en el "
                    f"departamento {q.departamento}, no en {departamento}."
                )
        return None

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
        provincia: str | None = None,
        distrito: str | None = None,
        quebrada: str | None = None,
    ) -> list[Alerta]:
        salida = []
        for a in self.alertas:
            q = self.quebradas.get(a.quebrada)
            if nivel and a.nivel != nivel:
                continue
            if departamento and (not q or q.departamento != departamento):
                continue
            if provincia and (not q or q.provincia != provincia):
                continue
            if distrito and (not q or q.distrito != distrito):
                continue
            if quebrada and a.quebrada != quebrada:
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
            if os.environ.get("SATQ_ALERTAS_AUTO", "0").strip() == "1":
                self.despachar_alerta(
                    quebrada, datos.PLANTILLAS["preventivo"]["texto"], "preventivo"
                )
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return resultado

    def validar_alerta(self, codigo: str, responsable: str) -> Alerta | None:
        with self._lock:
            a = self.alerta(codigo)
            cambio = False
            if a and a.estado == "pendiente":
                a.estado = "validada"
                a.fuente = "Autoridad · simulación"
                a.nota = f"Validada por {responsable} en el entorno de demostración."
                self.repo.guardar_alerta(a)
                cambio = True
            if (
                cambio
                and a is not None
                and a.nivel in ("alto", "critico")
                and os.environ.get("SATQ_ALERTAS_AUTO", "0").strip() == "1"
            ):
                self.despachar_alerta(
                    a.quebrada,
                    datos.PLANTILLAS["preventivo"]["texto"],
                    "preventivo",
                )
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
        self,
        quebrada: str,
        destinatarios: int,
        canales: list[str],
        texto: str = "",
        plantilla: str = "",
    ) -> list[Comunicacion]:
        with self._lock:
            destino = self._mascarar_destino(
                os.environ.get("SATQ_SMS_DESTINO", "").strip()
            )
            nuevas = []
            for canal in canales:
                clave = (
                    f"{quebrada}:{canal.strip().lower()}:{plantilla or 'general'}"
                )
                resultado = self._enviar_mensaje(canal, texto, clave)
                c = Comunicacion(
                    momento=self.ahora,
                    quebrada=quebrada,
                    destinatarios=destinatarios,
                    canal=canal,
                    resultado=resultado.estado,
                    entrega_real=resultado.entrega_real,
                    proveedor=resultado.proveedor,
                    id_externo=resultado.id_externo,
                    error=resultado.error,
                    intentos=resultado.intentos,
                    destino=destino,
                    clave_idempotencia=clave,
                )
                nuevas.append(c)
            self.repo.agregar_comunicaciones(nuevas)
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return nuevas

    @staticmethod
    def _mascarar_destino(destino: str) -> str:
        if not destino:
            return ""
        if len(destino) <= 7:
            return "****"
        return f"{destino[:3]}****{destino[-4:]}"

    def _enviar_mensaje(
        self, canal: str, texto: str, clave: str, destino: str | None = None
    ) -> ResultadoEnvio:
        if canal.strip().lower() != "sms":
            return ResultadoEnvio(estado="pendiente", proveedor="simulación")
        if not texto:
            return ResultadoEnvio(
                estado="fallido", proveedor="sms", error="Mensaje vacío."
            )
        if not modo_real():
            return obtener_canal("SMS").enviar("", texto)
        if clave in self._envios_realizados:
            return ResultadoEnvio(
                estado="pendiente",
                proveedor="simulación",
                error="Envío ya realizado para esta alerta.",
            )
        if destino is None:
            destino = os.environ.get("SATQ_SMS_DESTINO", "").strip()
        destino = destino.strip()
        if not destino:
            return ResultadoEnvio(
                estado="fallido",
                proveedor="sms",
                error="Destino SMS no configurado.",
            )
        permitidos = self._destinos_permitidos()
        abiertos = (
            os.environ.get("SATQ_SMS_PERMITIR_ABIERTOS", "0").strip() == "1"
        )
        if not abiertos:
            if not permitidos:
                return ResultadoEnvio(
                    estado="fallido",
                    proveedor="sms",
                    error="Sin destinos permitidos configurados.",
                )
            if destino not in permitidos:
                return ResultadoEnvio(
                    estado="fallido",
                    proveedor="sms",
                    error="Destino no permitido para la demostración.",
                )
        if len(self._envios_realizados) >= maximo_envios():
            return ResultadoEnvio(
                estado="fallido",
                proveedor="sms",
                error="Límite de envíos SMS alcanzado.",
            )
        resultado = obtener_canal("SMS").enviar(destino, texto)
        if resultado.estado == "enviado":
            self._envios_realizados.add(clave)
        return resultado

    @staticmethod
    def _destinos_permitidos() -> set[str]:
        crudo = os.environ.get("SATQ_SMS_DESTINOS_PERMITIDOS", "")
        permitidos = {x.strip() for x in crudo.split(",") if x.strip()}
        unico = os.environ.get("SATQ_SMS_DESTINO", "").strip()
        if unico:
            permitidos.add(unico)
        return permitidos

    @staticmethod
    def _normalizar_telefono(telefono: str) -> str:
        limpio = "".join(c for c in telefono if c.isdigit() or c == "+")
        if limpio.startswith("+"):
            return limpio
        digitos = limpio
        if len(digitos) == 9:
            return "+51" + digitos
        if len(digitos) == 11 and digitos.startswith("51"):
            return "+" + digitos
        return "+" + digitos if digitos else ""

    def suscribir(
        self,
        nombre: str,
        telefono: str,
        quebrada: str,
        consentimiento: bool,
        lat: float | None = None,
        lon: float | None = None,
        canal: str = "SMS",
    ) -> Suscriptor:
        with self._lock:
            if not consentimiento:
                raise ValueError("Se requiere consentimiento para suscribirse.")
            if quebrada not in self.quebradas:
                raise KeyError(quebrada)
            tel = self._normalizar_telefono(telefono)
            digitos = tel[1:] if tel.startswith("+") else tel
            if not (tel.startswith("+") and 8 <= len(digitos) <= 15):
                raise ValueError("Teléfono inválido. Usa formato +51XXXXXXXXX.")
            if lat is not None and lon is not None:
                cercana = self.quebrada_mas_cercana(lat, lon)
                if cercana is not None:
                    quebrada = cercana.codigo
            suscriptor = Suscriptor(
                telefono=tel,
                quebrada=quebrada,
                nombre=nombre.strip(),
                canal=canal,
                lat=lat,
                lon=lon,
                consentimiento=True,
                activo=True,
                creado=self.ahora,
            )
            self.repo.guardar_suscriptor(suscriptor)
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return suscriptor

    def baja_suscriptor(self, telefono: str, canal: str = "SMS") -> bool:
        with self._lock:
            ok = self.repo.desactivar_suscriptor(
                self._normalizar_telefono(telefono), canal
            )
            if ok and almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return ok

    def limpiar_suscriptores(self) -> int:
        with self._lock:
            total = len(self.suscriptores)
            self.repo.limpiar_suscriptores()
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return total

    def suscriptor_por_telefono(
        self, telefono: str, canal: str = "SMS"
    ) -> Suscriptor | None:
        buscado = self._normalizar_telefono(telefono)
        for suscriptor in self.suscriptores:
            if suscriptor.canal == canal and suscriptor.telefono == buscado:
                return suscriptor
        return None

    def suscriptor_por_chat(self, chat_id: str) -> Suscriptor | None:
        encontrados = [
            s for s in self.suscriptores if s.telegram_chat_id == str(chat_id)
        ]
        activos = [s for s in encontrados if s.activo]
        if activos:
            return activos[-1]
        return encontrados[-1] if encontrados else None

    def suscribir_telegram(
        self,
        nombre: str,
        telefono: str,
        quebrada: str,
        chat_id: str,
        usuario: str = "",
        lat: float | None = None,
        lon: float | None = None,
    ) -> Suscriptor:
        with self._lock:
            if not str(chat_id).strip():
                raise ValueError("chat_id es obligatorio.")
            if quebrada not in self.quebradas:
                raise KeyError(quebrada)
            tel = self._normalizar_telefono(telefono)
            digitos = tel[1:] if tel.startswith("+") else tel
            if not (tel.startswith("+") and 8 <= len(digitos) <= 15):
                raise ValueError("Teléfono inválido. Usa formato +51XXXXXXXXX.")
            if lat is not None and lon is not None:
                cercana = self.quebrada_mas_cercana(lat, lon)
                if cercana is not None:
                    quebrada = cercana.codigo
            existente = self.suscriptor_por_telefono(tel)
            for previo in self.suscriptores:
                if (
                    previo.telegram_chat_id == str(chat_id)
                    and previo.telefono != tel
                    and previo.activo
                ):
                    previo.activo = False
                    self.repo.guardar_suscriptor(previo)
            suscriptor = Suscriptor(
                telefono=tel,
                quebrada=quebrada,
                nombre=nombre.strip(),
                canal="SMS",
                lat=lat,
                lon=lon,
                consentimiento=True,
                activo=True,
                creado=existente.creado if existente else self.ahora,
                origen="telegram",
                telegram_chat_id=str(chat_id),
                telegram_usuario=usuario,
                verificado=False,
            )
            self.repo.guardar_suscriptor(suscriptor)
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return suscriptor

    @staticmethod
    def _hash_codigo(telefono: str, codigo: str) -> str:
        return hashlib.sha256(f"{telefono}:{codigo}".encode("utf-8")).hexdigest()

    def iniciar_verificacion(self, telefono: str) -> dict:
        with self._lock:
            suscriptor = self.suscriptor_por_telefono(telefono)
            if suscriptor is None:
                raise KeyError(telefono)
            ahora = datetime.now()
            ultimo = self._ultimo_codigo.get(suscriptor.telefono)
            if ultimo is not None and (ahora - ultimo).total_seconds() < 60:
                return {
                    "enviado": False,
                    "estado": "fallido",
                    "simulado": False,
                    "error": "Espera 60 segundos antes de pedir otro código.",
                    "telefono": self._mascarar_destino(suscriptor.telefono),
                }
            codigo = f"{secrets.randbelow(10000):04d}"
            self._ultimo_codigo[suscriptor.telefono] = ahora
            suscriptor.codigo_hash = self._hash_codigo(suscriptor.telefono, codigo)
            suscriptor.codigo_expira = datetime.now() + timedelta(minutes=10)
            suscriptor.intentos_codigo = 0
            suscriptor.verificado = False
            self.repo.guardar_suscriptor(suscriptor)
            texto = (
                f"SATQ DEMO: tu código de verificación es {codigo}. "
                "Vence en 10 minutos. No es alerta oficial."
            )
            resultado = self._enviar_mensaje(
                "SMS",
                texto,
                f"verificacion:{suscriptor.telefono}:{codigo}",
                destino=suscriptor.telefono,
            )
            self.repo.agregar_comunicaciones(
                [
                    Comunicacion(
                        momento=self.ahora,
                        quebrada=suscriptor.quebrada,
                        destinatarios=1,
                        canal="SMS",
                        resultado=resultado.estado,
                        entrega_real=resultado.entrega_real,
                        proveedor=resultado.proveedor,
                        id_externo=resultado.id_externo,
                        error=resultado.error,
                        intentos=resultado.intentos,
                        destino=self._mascarar_destino(suscriptor.telefono),
                        clave_idempotencia=(
                            f"verificacion:{suscriptor.telefono}:{codigo}"
                        ),
                    )
                ]
            )
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return {
                "enviado": resultado.estado in ("enviado", "pendiente"),
                "estado": resultado.estado,
                "simulado": resultado.estado == "pendiente",
                "error": resultado.error,
                "telefono": self._mascarar_destino(suscriptor.telefono),
            }

    def verificar_codigo(self, telefono: str, codigo: str) -> dict:
        with self._lock:
            suscriptor = self.suscriptor_por_telefono(telefono)
            if suscriptor is None:
                raise KeyError(telefono)
            if suscriptor.verificado:
                return {
                    "ok": True,
                    "ya_verificado": True,
                    "quebrada": suscriptor.quebrada,
                }
            if not suscriptor.codigo_hash or suscriptor.codigo_expira is None:
                return {"ok": False, "error": "No hay un código pendiente."}
            if datetime.now() > suscriptor.codigo_expira:
                return {"ok": False, "error": "El código venció. Solicita otro."}
            if suscriptor.intentos_codigo >= 3:
                return {"ok": False, "error": "Demasiados intentos. Solicita otro código."}
            if self._hash_codigo(suscriptor.telefono, codigo) != suscriptor.codigo_hash:
                suscriptor.intentos_codigo += 1
                self.repo.guardar_suscriptor(suscriptor)
                if almacen_postgres.habilitado():
                    almacen_postgres.guardar(self)
                return {
                    "ok": False,
                    "error": "Código incorrecto.",
                    "intentos": suscriptor.intentos_codigo,
                }
            suscriptor.verificado = True
            suscriptor.codigo_hash = ""
            suscriptor.codigo_expira = None
            suscriptor.intentos_codigo = 0
            self.repo.guardar_suscriptor(suscriptor)
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return {
                "ok": True,
                "quebrada": suscriptor.quebrada,
                "telefono": self._mascarar_destino(suscriptor.telefono),
            }

    def suscriptores_activos(self, quebrada: str | None = None) -> list[Suscriptor]:
        return [
            s
            for s in self.suscriptores
            if s.activo
            and s.verificado
            and (quebrada is None or s.quebrada == quebrada)
        ]

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        radio = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        return 2 * radio * math.asin(math.sqrt(a))

    def quebrada_mas_cercana(self, lat: float, lon: float) -> Quebrada | None:
        mejor: Quebrada | None = None
        mejor_distancia: float | None = None
        for q in self.quebradas.values():
            distancia = self._haversine(lat, lon, q.lat, q.lon)
            if mejor_distancia is None or distancia < mejor_distancia:
                mejor = q
                mejor_distancia = distancia
        return mejor

    def despachar_alerta(
        self, quebrada: str, texto: str, plantilla: str = "preventivo"
    ) -> list[Comunicacion]:
        with self._lock:
            nuevas = []
            for suscriptor in self.suscriptores_activos(quebrada):
                clave = (
                    f"{suscriptor.quebrada}:{suscriptor.canal.lower()}:"
                    f"{plantilla}:{suscriptor.telefono}"
                )
                resultado = self._enviar_mensaje(
                    suscriptor.canal, texto, clave, destino=suscriptor.telefono
                )
                nuevas.append(
                    Comunicacion(
                        momento=self.ahora,
                        quebrada=suscriptor.quebrada,
                        destinatarios=1,
                        canal=suscriptor.canal,
                        resultado=resultado.estado,
                        entrega_real=resultado.entrega_real,
                        proveedor=resultado.proveedor,
                        id_externo=resultado.id_externo,
                        error=resultado.error,
                        intentos=resultado.intentos,
                        destino=self._mascarar_destino(suscriptor.telefono),
                        clave_idempotencia=clave,
                    )
                )
            self.repo.agregar_comunicaciones(nuevas)
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return nuevas

    def enviar_prueba(self, telefono: str) -> dict:
        """Envía un SMS de prueba solo al teléfono indicado."""
        with self._lock:
            suscriptor = self.suscriptor_por_telefono(telefono)
            if suscriptor is None:
                raise KeyError(telefono)
            texto = (
                "SATQ DEMO: este es un SMS de prueba para tu suscripción. "
                "Recibirás avisos si el riesgo de huaico es alto en tu zona. "
                "No es una alerta oficial."
            )
            clave = f"prueba:{suscriptor.telefono}:{datetime.now().isoformat()}"
            resultado = self._enviar_mensaje(
                "SMS", texto, clave, destino=suscriptor.telefono
            )
            self.repo.agregar_comunicaciones(
                [
                    Comunicacion(
                        momento=self.ahora,
                        quebrada=suscriptor.quebrada,
                        destinatarios=1,
                        canal="SMS",
                        resultado=resultado.estado,
                        entrega_real=resultado.entrega_real,
                        proveedor=resultado.proveedor,
                        id_externo=resultado.id_externo,
                        error=resultado.error,
                        intentos=resultado.intentos,
                        destino=self._mascarar_destino(suscriptor.telefono),
                        clave_idempotencia=clave,
                    )
                ]
            )
            if almacen_postgres.habilitado():
                almacen_postgres.guardar(self)
            return {
                "estado": resultado.estado,
                "proveedor": resultado.proveedor,
                "error": resultado.error,
                "simulado": resultado.estado == "pendiente",
            }

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
