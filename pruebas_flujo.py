"""Pruebas de los flujos interactivos contra un servidor en marcha.

    python servidor_demo.py        (en una terminal)
    python pruebas_flujo.py        (en otra)

Comprueba que las acciones del prototipo hacen lo que dicen: validar una
alerta, cambiar su estado, registrar un envío simulado, guardar umbrales,
rechazar umbrales inválidos y dar de alta una quebrada.
"""

from __future__ import annotations

import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000"
fallos: list[str] = []


def get(ruta: str) -> str:
    return urllib.request.urlopen(BASE + ruta).read().decode("utf-8")


def post(ruta: str, campos: list[tuple[str, str]]) -> str:
    datos = urllib.parse.urlencode(campos).encode()
    peticion = urllib.request.Request(BASE + ruta, data=datos, method="POST")
    try:
        return urllib.request.urlopen(peticion).read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8")


def comprobar(nombre: str, condicion: bool, detalle: str = "") -> None:
    if condicion:
        print(f"  OK    {nombre}")
    else:
        fallos.append(nombre)
        print(f"  FALLA {nombre} {detalle}")


def fila_de(html: str, quebrada: str) -> str:
    m = re.search(r"<tr[^>]*>(?:(?!</tr>).)*?" + quebrada + r".*?</tr>", html, re.S)
    return m.group(0) if m else ""


def main() -> int:
    print("Pruebas de flujo · SATQ Digital\n")

    print("1. Alerta crítica pendiente al inicio")
    html = get("/alertas")
    comprobar("Huaycoloro aparece como crítico", "Crítico" in fila_de(html, "Huaycoloro"))
    comprobar("y está pendiente de revisión",
              "Pendiente de revisión" in fila_de(html, "Huaycoloro"))

    print("\n2. Validar la alerta")
    post("/alertas/validar", [("alerta", "AL-0007")])
    html = get("/alertas?estado=todas")
    comprobar("pasa a Validada", "Validada" in fila_de(html, "Huaycoloro"))

    print("\n3. Cambiar el estado a Enviada")
    post("/alertas/estado", [("alerta", "AL-0007"), ("nuevo_estado", "enviada")])
    html = get("/alertas?estado=todas")
    comprobar("pasa a Enviada", "Enviada" in fila_de(html, "Huaycoloro"))

    print("\n4. Confirmar un envío simulado")
    antes = get("/notificaciones").count("Pendiente · simulación")
    post("/notificaciones/confirmar",
         [("quebrada", "huaycoloro"), ("canales", "SMS"), ("canales", "WhatsApp")])
    despues = get("/notificaciones").count("Pendiente · simulación")
    comprobar("se añaden dos registros al historial", despues == antes + 2,
              f"(antes {antes}, después {despues})")

    print("\n5. Guardar umbrales nuevos (crítico 50 mm)")
    post("/configuracion/umbrales",
         [("bajo", "0"), ("moderado", "20"), ("alto", "30"),
          ("critico", "50"), ("ventana", "6")])
    html = get("/quebrada/huaycoloro")
    bloque = html.split("Riesgo actual")[1][:400]
    comprobar("Huaycoloro baja de Crítico a Alto", "Alto" in bloque and "Crítico" not in bloque)
    comprobar("queda registrado en el historial de parámetros",
              "Crítico: 50 mm/6 h" in get("/configuracion"))

    print("\n6. Rechazar umbrales inválidos (alto menor que moderado)")
    html = post("/configuracion/umbrales",
                [("bajo", "0"), ("moderado", "30"), ("alto", "20"),
                 ("critico", "40"), ("ventana", "6")])
    comprobar("muestra el error y no guarda", "estrictamente crecientes" in html)

    print("\n7. Registrar una quebrada nueva")
    post("/configuracion/quebrada",
         [("nombre", "Quebrada Prueba"), ("departamento", "Ayacucho"),
          ("provincia", "Huamanga"), ("distrito", "Carmen Alto")])
    html = get("/quebradas?departamento=Ayacucho")
    comprobar("aparece en el listado", "Quebrada Prueba" in html)
    comprobar("y sin lecturas se marca Sin datos",
              "Sin dato" in fila_de(html, "Quebrada Prueba"))

    print("\n8. Restituir el escenario")
    post("/configuracion/umbrales",
         [("bajo", "0"), ("moderado", "20"), ("alto", "30"),
          ("critico", "40"), ("ventana", "6")])
    comprobar("Huaycoloro vuelve a Crítico",
              "Crítico" in get("/quebrada/huaycoloro").split("Riesgo actual")[1][:300])

    print()
    if fallos:
        print(f"{len(fallos)} prueba(s) fallaron: {', '.join(fallos)}")
        return 1
    print("Todas las pruebas pasaron.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
