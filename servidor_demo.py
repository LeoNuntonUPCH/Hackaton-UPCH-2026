"""SATQ Digital — servidor de respaldo, sin FastAPI.

Sirve exactamente las mismas pantallas que `app.py`, usando solo la librería
estándar de Python más Jinja2 (que viene incluido en Anaconda). Está aquí por
una razón práctica: si la PC donde se hace la demostración no tiene FastAPI
instalado ni acceso a internet para instalarlo, la demostración igual corre.

    python servidor_demo.py

Luego abrir http://127.0.0.1:8000

La versión completa, con la API documentada en /docs, es `app.py`.
"""

from __future__ import annotations

import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from satq import vistas
from satq.estado import ESTADO
from satq.plantillas import DIR_ESTATICOS, render

PUERTO = 8000

RUTAS_GET = {
    "/dashboard": vistas.dashboard,
    "/mapa": vistas.mapa,
    "/quebradas": vistas.quebradas,
    "/alertas": vistas.alertas,
    "/notificaciones": vistas.notificaciones,
    "/notificaciones/confirmar": vistas.confirmacion,
    "/reportes": vistas.reportes,
    "/configuracion": vistas.configuracion,
    "/login": vistas.login,
}


def _aplanar(consulta: dict[str, list[str]]) -> dict:
    """parse_qs devuelve listas; se dejan listas solo donde hacen falta."""
    salida: dict = {}
    for clave, valores in consulta.items():
        salida[clave] = valores if clave == "canales" else valores[0]
    return salida


class Manejador(BaseHTTPRequestHandler):
    server_version = "SATQ-demo"

    def log_message(self, formato, *args):  # noqa: N802  (API de la stdlib)
        sys.stderr.write("  %s\n" % (formato % args))

    # -- utilidades ----------------------------------------------------

    def _responder(self, cuerpo: str, codigo: int = 200,
                   tipo: str = "text/html; charset=utf-8") -> None:
        datos = cuerpo.encode("utf-8") if isinstance(cuerpo, str) else cuerpo
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _redirigir(self, destino: str) -> None:
        self.send_response(303)
        self.send_header("Location", destino)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _estatico(self, ruta: str) -> None:
        relativa = ruta[len("/static/"):].lstrip("/")
        archivo = (DIR_ESTATICOS / relativa).resolve()
        if not str(archivo).startswith(str(Path(DIR_ESTATICOS).resolve())) \
                or not archivo.is_file():
            self._responder("No encontrado", 404, "text/plain; charset=utf-8")
            return
        tipo = mimetypes.guess_type(str(archivo))[0] or "application/octet-stream"
        datos = archivo.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _formulario(self) -> dict:
        largo = int(self.headers.get("Content-Length") or 0)
        crudo = self.rfile.read(largo).decode("utf-8") if largo else ""
        return _aplanar(parse_qs(crudo, keep_blank_values=True))

    # -- verbos --------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        partes = urlparse(self.path)
        ruta = partes.path.rstrip("/") or "/"
        params = _aplanar(parse_qs(partes.query, keep_blank_values=True))

        if partes.path.startswith("/static/"):
            self._estatico(partes.path)
            return

        if ruta == "/":
            self._redirigir("/login")
            return

        if ruta.startswith("/quebrada/"):
            codigo = ruta.split("/quebrada/", 1)[1]
            self._responder(render(*vistas.quebrada(ESTADO, {"codigo": codigo})))
            return

        vista = RUTAS_GET.get(ruta)
        if vista is None:
            self._responder(
                render(*vistas.quebrada(ESTADO, {"codigo": "__inexistente__"})), 404
            )
            return

        self._responder(render(*vista(ESTADO, params)))

    def do_POST(self) -> None:  # noqa: N802
        ruta = urlparse(self.path).path.rstrip("/") or "/"
        datos = self._formulario()

        if ruta == "/login":
            from satq.datos import USUARIOS

            ESTADO.usuario = USUARIOS.get(
                (datos.get("correo") or "").strip().lower(),
                USUARIOS["maria.torres@ejemplo.pe"],
            )
            self._redirigir("/dashboard")
        elif ruta == "/alertas/validar":
            self._redirigir(vistas.accion_validar(ESTADO, datos))
        elif ruta == "/alertas/estado":
            self._redirigir(vistas.accion_estado_alerta(ESTADO, datos))
        elif ruta == "/notificaciones/confirmar":
            self._redirigir(vistas.accion_confirmar_envio(ESTADO, datos))
        elif ruta == "/configuracion/umbrales":
            destino, errores = vistas.accion_umbrales(ESTADO, datos)
            if errores:
                self._responder(
                    render(
                        *vistas.configuracion(
                            ESTADO, {"errores": errores, "pestana": "umbrales"}
                        )
                    )
                )
            else:
                self._redirigir(destino)
        elif ruta == "/configuracion/quebrada":
            self._redirigir(vistas.accion_nueva_quebrada(ESTADO, datos))
        else:
            self._responder("No encontrado", 404, "text/plain; charset=utf-8")


def main(puerto: int = PUERTO) -> None:
    servidor = ThreadingHTTPServer(("127.0.0.1", puerto), Manejador)
    print("SATQ Digital · servidor de demostración (sin FastAPI)")
    print(f"  Abre http://127.0.0.1:{puerto} en tu navegador")
    print("  Ctrl+C para detener\n")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        servidor.server_close()


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else PUERTO)
