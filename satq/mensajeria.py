"""Envío real de mensajes por WhatsApp y SMS, usando la API REST de Twilio.

Deliberadamente no usa el SDK `twilio` (paquete de PyPI): la API de Twilio es
HTTP simple con autenticación básica, así que `urllib` —que viene con
Python— alcanza. Esto evita instalar una dependencia nueva y mantiene la
misma filosofía del resto del proyecto: cero librerías externas.

Este módulo nunca lanza una excepción hacia quien lo llama. Si algo falla
—no hay credenciales, no hay red, Twilio rechaza el número— devuelve un
`Resultado` con el motivo, para que el llamador decida qué hacer. El
prototipo sigue funcionando en modo simulado si este módulo no está
configurado; esa es la condición por defecto.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RUTA_ENV = RAIZ / ".env"

_API_BASE_DEFECTO = "https://api.twilio.com"


def _cargar_env(ruta: Path = RUTA_ENV) -> None:
    """Carga variables desde un archivo .env a os.environ, sin pisar las que
    ya estén definidas (así una variable de entorno real del sistema
    siempre gana sobre el archivo). Formato simple: CLAVE=valor por línea,
    '#' inicia un comentario, líneas vacías se ignoran. No requiere
    python-dotenv.
    """
    if not ruta.is_file():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        clave = clave.strip()
        valor = valor.strip().strip('"').strip("'")
        if clave and clave not in os.environ:
            os.environ[clave] = valor


_cargar_env()


@dataclass(frozen=True)
class ConfigTwilio:
    account_sid: str
    auth_token: str
    whatsapp_from: str | None   # formato Twilio: "whatsapp:+14155238886"
    sms_from: str | None
    whatsapp_content_sid: str | None  # plantilla aprobada, formato "HX..."
    api_base: str = _API_BASE_DEFECTO


@dataclass(frozen=True)
class Resultado:
    exito: bool
    estado: str          # queued | sent | failed | sin_configurar | sin_red | ...
    sid: str | None = None
    error: str | None = None

    @property
    def texto_legible(self) -> str:
        if self.exito:
            return f"Enviado · sid {self.sid}" if self.sid else "Enviado"
        return self.error or "Fallido"


def configuracion() -> ConfigTwilio | None:
    """Lee la configuración de variables de entorno. None si falta lo
    imprescindible (SID y token): en ese caso el llamador debe simular.
    """
    sid = os.environ.get("TWILIO_ACCOUNT_SID", "").strip()
    token = os.environ.get("TWILIO_AUTH_TOKEN", "").strip()
    if not sid or not token:
        return None
    return ConfigTwilio(
        account_sid=sid,
        auth_token=token,
        whatsapp_from=os.environ.get("TWILIO_WHATSAPP_FROM", "").strip() or None,
        sms_from=os.environ.get("TWILIO_SMS_FROM", "").strip() or None,
        whatsapp_content_sid=os.environ.get("TWILIO_WHATSAPP_CONTENT_SID", "").strip() or None,
        api_base=os.environ.get("TWILIO_API_BASE", _API_BASE_DEFECTO).rstrip("/"),
    )


def credenciales_disponibles() -> bool:
    """Hay algún proveedor configurado: Telegram, Meta (WhatsApp) o Twilio."""
    return (configuracion() is not None
            or configuracion_meta() is not None
            or configuracion_telegram() is not None)


def estado_canal(canal: str) -> dict:
    """Para la interfaz: si el canal está listo para enviar de verdad.

    `canal` es "whatsapp" o "sms". Devuelve un dict con 'conectado' (bool)
    y 'detalle' (texto corto para mostrar junto al nombre del canal).

    WhatsApp puede ir por Meta (preferente) o por Twilio; SMS solo por
    Twilio, que es quien provee números; Telegram por su propio bot.
    """
    if canal == "telegram":
        if configuracion_telegram() is None:
            return {"conectado": False, "detalle": "no conectado"}
        if not destinatarios_de("telegram"):
            return {"conectado": False,
                    "detalle": "bot listo · falta TELEGRAM_CHAT_IDS"}
        return {"conectado": True, "detalle": "conectado · bot de Telegram"}

    if canal == "whatsapp":
        meta = configuracion_meta()
        if meta is not None:
            if not destinatarios_prueba():
                return {"conectado": False,
                        "detalle": "Meta listo · falta TWILIO_DESTINATARIOS_PRUEBA"}
            return {"conectado": True, "detalle": "conectado · Meta Cloud API"}

    cfg = configuracion()
    if cfg is None:
        return {"conectado": False, "detalle": "no conectado"}
    remitente = cfg.whatsapp_from if canal == "whatsapp" else cfg.sms_from
    if not remitente:
        return {"conectado": False, "detalle": "credenciales sin número de origen"}
    if not destinatarios_prueba():
        return {"conectado": False,
                "detalle": "remitente listo · falta TWILIO_DESTINATARIOS_PRUEBA"}
    return {"conectado": True, "detalle": f"conectado · {remitente}"}


def lista_canales() -> list[dict]:
    """Para la pantalla de Notificaciones: estado real de WhatsApp y SMS,
    en el mismo formato que antes tenía datos.CANALES (nombre/conectado),
    con 'detalle' agregado para que la interfaz pueda mostrar el motivo.
    """
    salida = []
    for nombre, clave in (("WhatsApp", "whatsapp"), ("SMS", "sms"),
                           ("Telegram", "telegram")):
        est = estado_canal(clave)
        salida.append({"nombre": nombre, "conectado": est["conectado"],
                        "detalle": est["detalle"]})
    return salida


def canales_listos() -> list[str]:
    """Nombres de los canales que pueden enviar de verdad ahora mismo:
    con proveedor configurado y con destinatarios cargados.
    """
    return [c["nombre"] for c in lista_canales() if c["conectado"]]


def hay_envio_real() -> bool:
    """True si al menos un canal puede enviar de verdad. La interfaz lo usa
    para decidir entre decir "Simular envío" o "Enviar de verdad".
    """
    return bool(canales_listos())


def destinatarios_de(canal: str) -> list[str]:
    """Destinatarios del canal indicado.

    Cada canal identifica a la gente de forma distinta: WhatsApp y SMS por
    número de teléfono, Telegram por `chat_id`. Por eso no hay una sola
    lista de destinatarios, sino una por canal.
    """
    if canal.lower() == "telegram":
        crudo = os.environ.get("TELEGRAM_CHAT_IDS", "")
    else:
        crudo = os.environ.get("TWILIO_DESTINATARIOS_PRUEBA", "")
    return [n.strip() for n in crudo.split(",") if n.strip()]


def destinatarios_prueba() -> list[str]:
    """Números reales de prueba para la demo, separados por coma en
    TWILIO_DESTINATARIOS_PRUEBA. Vacío si no se configuró ninguno: el envío
    real entonces no tiene a quién llegar, y el llamador debe simular.
    """
    crudo = os.environ.get("TWILIO_DESTINATARIOS_PRUEBA", "")
    return [n.strip() for n in crudo.split(",") if n.strip()]


# --------------------------------------------------------------------------
# Proveedor: Telegram Bot API
#
# Es el canal que funciona sin verificación de empresa, sin tarjeta y sin
# saldo: basta crear un bot con @BotFather. Se incorporó porque ni la cuenta
# de prueba de Twilio ni el alta en Meta resultaron viables en el plazo del
# proyecto (ver GUIA_MENSAJERIA.md).
#
# Igual que WhatsApp, Telegram exige que la persona escriba primero al bot:
# un bot no puede iniciar una conversación. La diferencia es que ese permiso
# no caduca a las 24 h.
# --------------------------------------------------------------------------

_TELEGRAM_BASE_DEFECTO = "https://api.telegram.org"


@dataclass(frozen=True)
class ConfigTelegram:
    token: str
    api_base: str = _TELEGRAM_BASE_DEFECTO


def configuracion_telegram() -> ConfigTelegram | None:
    """Lee la configuración de Telegram. None si falta el token."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        return None
    return ConfigTelegram(
        token=token,
        api_base=os.environ.get("TELEGRAM_API_BASE",
                                 _TELEGRAM_BASE_DEFECTO).rstrip("/"),
    )


def enviar_telegram(chat_id: str, texto: str) -> Resultado:
    """Envía un mensaje por Telegram. `chat_id` es el identificador numérico
    de la conversación, que se obtiene con `obtener_chat_id.py`.
    """
    cfg = configuracion_telegram()
    if cfg is None:
        return Resultado(exito=False, estado="sin_configurar",
                          error="Telegram no está configurado (falta TELEGRAM_BOT_TOKEN)")

    url = f"{cfg.api_base}/bot{cfg.token}/sendMessage"
    cuerpo = json.dumps({"chat_id": chat_id, "text": texto}).encode()
    peticion = urllib.request.Request(
        url, data=cuerpo,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=15) as resp:
            datos = json.loads(resp.read().decode())
            if not datos.get("ok"):
                return Resultado(exito=False, estado="failed",
                                  error=f"Telegram rechazó el envío: {datos.get('description')}")
            mensaje_id = (datos.get("result") or {}).get("message_id")
            return Resultado(exito=True, estado="enviado", sid=str(mensaje_id))
    except urllib.error.HTTPError as e:
        try:
            detalle = json.loads(e.read().decode())
            msg = detalle.get("description", str(e))
        except Exception:  # noqa: BLE001 — el cuerpo de error no siempre es JSON
            msg = str(e)
        return Resultado(exito=False, estado="failed",
                          error=f"Telegram rechazó el envío: {msg}")
    except urllib.error.URLError as e:
        return Resultado(exito=False, estado="sin_red",
                          error=f"Sin conexión a Telegram: {e.reason}")
    except Exception as e:  # noqa: BLE001 — nunca debe tumbar al llamador
        return Resultado(exito=False, estado="error", error=f"Error inesperado: {e}")


# --------------------------------------------------------------------------
# Proveedor alternativo: Meta WhatsApp Cloud API (la API oficial de WhatsApp)
#
# Se añadió porque una cuenta Twilio de prueba no permite enviar WhatsApp por
# código: las plantillas (Content API) requieren cuenta de pago. Meta, en
# cambio, da un número de prueba gratuito que envía a una lista corta de
# destinatarios verificados, sin tarjeta y sin saldo.
#
# Dentro de una ventana de servicio de 24 h —que se abre cuando la persona
# escribe primero al número— se puede enviar texto libre sin plantilla.
# --------------------------------------------------------------------------

_META_BASE_DEFECTO = "https://graph.facebook.com"
_META_VERSION_DEFECTO = "v21.0"


@dataclass(frozen=True)
class ConfigMeta:
    token: str
    phone_id: str          # "Phone number ID" de la app, no el número en sí
    version: str = _META_VERSION_DEFECTO
    api_base: str = _META_BASE_DEFECTO


def configuracion_meta() -> ConfigMeta | None:
    """Lee la configuración de Meta. None si falta token o phone_id."""
    token = os.environ.get("META_WHATSAPP_TOKEN", "").strip()
    phone_id = os.environ.get("META_WHATSAPP_PHONE_ID", "").strip()
    if not token or not phone_id:
        return None
    return ConfigMeta(
        token=token,
        phone_id=phone_id,
        version=os.environ.get("META_WHATSAPP_VERSION", _META_VERSION_DEFECTO).strip()
                 or _META_VERSION_DEFECTO,
        api_base=os.environ.get("META_API_BASE", _META_BASE_DEFECTO).rstrip("/"),
    )


def _solo_digitos(numero: str) -> str:
    """Meta espera el número sin '+' ni separadores: 51963227613."""
    return "".join(c for c in numero if c.isdigit())


def enviar_whatsapp_meta(destino: str, texto: str) -> Resultado:
    """Envía por la API oficial de Meta. Texto libre, que es gratis mientras
    la ventana de 24 h esté abierta (la abre la persona al escribir primero).
    """
    cfg = configuracion_meta()
    if cfg is None:
        return Resultado(exito=False, estado="sin_configurar",
                          error="Meta no está configurado (faltan META_WHATSAPP_* en .env)")

    url = f"{cfg.api_base}/{cfg.version}/{cfg.phone_id}/messages"
    cuerpo = json.dumps({
        "messaging_product": "whatsapp",
        "to": _solo_digitos(destino),
        "type": "text",
        "text": {"body": texto},
    }).encode()

    peticion = urllib.request.Request(
        url,
        data=cuerpo,
        headers={
            "Authorization": f"Bearer {cfg.token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=15) as resp:
            datos = json.loads(resp.read().decode())
            mensajes = datos.get("messages") or [{}]
            return Resultado(exito=True, estado="enviado",
                              sid=mensajes[0].get("id"))
    except urllib.error.HTTPError as e:
        try:
            detalle = json.loads(e.read().decode())
            err = detalle.get("error", {})
            msg = err.get("message", str(e))
            if err.get("error_user_msg"):
                msg = f"{msg} — {err['error_user_msg']}"
        except Exception:  # noqa: BLE001 — el cuerpo de error no siempre es JSON
            msg = str(e)
        return Resultado(exito=False, estado="failed",
                          error=f"Meta rechazó el envío: {msg}")
    except urllib.error.URLError as e:
        return Resultado(exito=False, estado="sin_red",
                          error=f"Sin conexión a Meta: {e.reason}")
    except Exception as e:  # noqa: BLE001 — nunca debe tumbar al llamador
        return Resultado(exito=False, estado="error", error=f"Error inesperado: {e}")


def _enviar(
    cfg: ConfigTwilio, *, de: str, a: str, cuerpo: str | None = None,
    content_sid: str | None = None, content_variables: str | None = None,
) -> Resultado:
    """Envia un mensaje. Con `cuerpo` manda texto libre (Body); con
    `content_sid` manda una plantilla aprobada, obligatorio para WhatsApp
    cuando el mensaje lo inicia la empresa (politica vigente desde abril
    de 2025, error 63016 / "ContentSid Required").
    """
    url = f"{cfg.api_base}/2010-04-01/Accounts/{cfg.account_sid}/Messages.json"
    campos = {"From": de, "To": a}
    if content_sid:
        campos["ContentSid"] = content_sid
        if content_variables:
            campos["ContentVariables"] = content_variables
    else:
        campos["Body"] = cuerpo or ""
    datos = urllib.parse.urlencode(campos).encode()
    credencial = base64.b64encode(f"{cfg.account_sid}:{cfg.auth_token}".encode()).decode()
    peticion = urllib.request.Request(
        url,
        data=datos,
        headers={
            "Authorization": f"Basic {credencial}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=10) as resp:
            cuerpo_resp = json.loads(resp.read().decode())
            return Resultado(
                exito=True,
                estado=cuerpo_resp.get("status", "queued"),
                sid=cuerpo_resp.get("sid"),
            )
    except urllib.error.HTTPError as e:
        try:
            detalle = json.loads(e.read().decode())
            msg = detalle.get("message", str(e))
        except Exception:  # noqa: BLE001 — el cuerpo de error no siempre es JSON
            msg = str(e)
        return Resultado(exito=False, estado="failed", error=f"Twilio rechazó el envío: {msg}")
    except urllib.error.URLError as e:
        return Resultado(exito=False, estado="sin_red", error=f"Sin conexión a Twilio: {e.reason}")
    except Exception as e:  # noqa: BLE001 — nunca debe tumbar al llamador
        return Resultado(exito=False, estado="error", error=f"Error inesperado: {e}")


def enviar_whatsapp(destino: str, texto: str) -> Resultado:
    """`destino` en formato internacional, p. ej. +51987654321.

    Si hay configuración de Meta (META_WHATSAPP_*), se usa la API oficial
    de WhatsApp, que es la vía que funciona sin cuenta de pago. Si no, se
    intenta por Twilio.

    Con Twilio, el sandbox exige que el número se haya unido antes enviando
    el código "join <palabra>"; y desde abril de 2025 los mensajes que
    inicia la empresa requieren una plantilla aprobada, que a su vez
    requiere cuenta de pago. Por eso Meta es el camino recomendado aquí.
    """
    if configuracion_meta() is not None:
        return enviar_whatsapp_meta(destino, texto)

    cfg = configuracion()
    if cfg is None:
        return Resultado(exito=False, estado="sin_configurar",
                          error="Twilio no está configurado (falta .env)")
    if not cfg.whatsapp_from:
        return Resultado(exito=False, estado="sin_configurar",
                          error="Falta TWILIO_WHATSAPP_FROM en .env")
    destino_fmt = destino if destino.startswith("whatsapp:") else f"whatsapp:{destino}"
    if cfg.whatsapp_content_sid:
        variables = json.dumps({"1": texto})
        return _enviar(cfg, de=cfg.whatsapp_from, a=destino_fmt,
                        content_sid=cfg.whatsapp_content_sid,
                        content_variables=variables)
    return _enviar(cfg, de=cfg.whatsapp_from, a=destino_fmt, cuerpo=texto)


def enviar_sms(destino: str, texto: str) -> Resultado:
    cfg = configuracion()
    if cfg is None:
        return Resultado(exito=False, estado="sin_configurar",
                          error="Twilio no está configurado (falta .env)")
    if not cfg.sms_from:
        return Resultado(exito=False, estado="sin_configurar",
                          error="Falta TWILIO_SMS_FROM en .env")
    return _enviar(cfg, de=cfg.sms_from, a=destino, cuerpo=texto)


def enviar(canal: str, destino: str, texto: str) -> Resultado:
    """Punto de entrada único: despacha según el nombre de canal usado en
    la interfaz ("WhatsApp", "SMS" o "Telegram").
    """
    clave = canal.lower()
    if clave == "whatsapp":
        return enviar_whatsapp(destino, texto)
    if clave == "sms":
        return enviar_sms(destino, texto)
    if clave == "telegram":
        return enviar_telegram(destino, texto)
    return Resultado(exito=False, estado="error", error=f"Canal desconocido: {canal}")
