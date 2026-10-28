"""Diagnóstico de arranque del SATQ Digital.

Si el servidor no levanta, ejecuta:

    python diagnostico.py

Dice exactamente qué falta o qué falla, en vez de dejar un traceback largo.
No necesita ninguna dependencia: funciona siempre.
"""

from __future__ import annotations

import os
import sys
import traceback

ANCHO = 62


def titulo(texto: str) -> None:
    print("\n" + texto)
    print("-" * ANCHO)


def main() -> int:
    print("=" * ANCHO)
    print("  SATQ Digital · diagnóstico de arranque")
    print("=" * ANCHO)

    problemas: list[str] = []

    titulo("1. Intérprete de Python")
    print(f"  Versión    : {sys.version.split()[0]}")
    print(f"  Ejecutable : {sys.executable}")
    print(f"  Carpeta    : {os.getcwd()}")
    if sys.version_info < (3, 9):
        problemas.append("Se necesita Python 3.9 o superior.")

    titulo("2. Archivos del proyecto")
    requeridos = [
        "app.py",
        "servidor_demo.py",
        os.path.join("satq", "motor.py"),
        os.path.join("satq", "vistas.py"),
        os.path.join("satq", "templates", "base.html"),
        os.path.join("satq", "static", "css", "satq.css"),
    ]
    for ruta in requeridos:
        existe = os.path.isfile(ruta)
        print(f"  {'OK   ' if existe else 'FALTA'} {ruta}")
        if not existe:
            problemas.append(f"Falta el archivo {ruta}.")
    if not os.path.isfile("app.py"):
        problemas.append(
            "Estás ejecutando desde otra carpeta. Haz primero:\n"
            "      cd C:\\Users\\<usuario>\\Downloads\\Hackaton-UPCH-2026"
        )

    titulo("3. Dependencias")
    estado: dict[str, bool] = {}
    for paquete, obligatorio in (("jinja2", True), ("fastapi", False),
                                 ("uvicorn", False)):
        try:
            modulo = __import__(paquete)
            version = getattr(modulo, "__version__", "?")
            estado[paquete] = True
            print(f"  OK      {paquete:10s} {version}")
        except Exception as e:  # noqa: BLE001
            estado[paquete] = False
            print(f"  NO      {paquete:10s} ({type(e).__name__})")
            if obligatorio:
                problemas.append(
                    f"Falta {paquete}, que es imprescindible. "
                    f"Instálalo con:  pip install {paquete}"
                )

    titulo("4. Carga del paquete satq")
    try:
        from satq import vistas  # noqa: F401
        from satq.estado import ESTADO
        from satq.plantillas import render

        ev = ESTADO.evaluacion("huaycoloro")
        print(f"  OK    motor de umbrales: {ev.acumulado} mm/6 h -> {ev.etiqueta}")
        html = render(*vistas.dashboard(ESTADO, {}))
        print(f"  OK    plantillas: dashboard renderiza {len(html)} bytes")
    except Exception:
        print("  FALLA al cargar el paquete satq:\n")
        traceback.print_exc()
        problemas.append("El paquete satq no carga (ver el detalle de arriba).")

    if estado.get("fastapi") and estado.get("uvicorn"):
        titulo("5. Carga de la aplicación FastAPI")
        try:
            import app as aplicacion

            rutas = len(getattr(aplicacion.app, "routes", []))
            print(f"  OK    app.py carga correctamente ({rutas} rutas)")
        except Exception:
            print("  FALLA al importar app.py:\n")
            traceback.print_exc()
            problemas.append(
                "app.py no carga. Usa el servidor de respaldo mientras tanto:\n"
                "      python servidor_demo.py"
            )
    else:
        titulo("5. Carga de la aplicación FastAPI")
        print("  Omitido: FastAPI o Uvicorn no están instalados.")
        print("  El prototipo funciona igual con:  python servidor_demo.py")

    print("\n" + "=" * ANCHO)
    if problemas:
        print(f"  {len(problemas)} problema(s) encontrado(s):\n")
        for i, p in enumerate(problemas, 1):
            print(f"  {i}. {p}")
        print("\n  En cualquier caso, esto casi siempre funciona:")
        print("      python servidor_demo.py")
        print("=" * ANCHO)
        return 1

    print("  Todo correcto. Arranca con:")
    if estado.get("fastapi") and estado.get("uvicorn"):
        print("      python -m uvicorn app:app --port 8000")
    print("      python servidor_demo.py")
    print("=" * ANCHO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
