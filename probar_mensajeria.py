"""Prueba rápida: envía un mensaje real por cada canal configurado en .env.

    python probar_mensajeria.py

Funciona con cualquier proveedor que esté configurado (Telegram, Meta
WhatsApp o Twilio). Si no hay ninguno, lo dice y no falla.
"""
import sys

sys.path.insert(0, ".")
from satq import mensajeria  # noqa: E402

TEXTO = (
    "SATQ Digital: mensaje de prueba. Si lees esto, el canal de alertas "
    "esta funcionando correctamente."
)


def main() -> int:
    canales = mensajeria.canales_listos()
    if not canales:
        print("Ningun canal esta configurado todavia.")
        print()
        print("Para Telegram necesitas en .env:")
        print("  TELEGRAM_BOT_TOKEN=<token de @BotFather>")
        print("  TELEGRAM_CHAT_IDS=<obtenlo con: python obtener_chat_id.py>")
        print()
        print("Detalle por canal:")
        for c in mensajeria.lista_canales():
            print(f"  - {c['nombre']}: {c['detalle']}")
        return 1

    print("Canales listos:", ", ".join(canales))
    print()

    fallos = 0
    for canal in canales:
        destinos = mensajeria.destinatarios_de(canal)
        if not destinos:
            print(f"[{canal}] sin destinatarios en .env — se omite.")
            fallos += 1
            continue
        for destino in destinos:
            print(f"[{canal}] enviando a {destino} ...")
            r = mensajeria.enviar(canal, destino, TEXTO)
            print(f"    exito  : {r.exito}")
            print(f"    estado : {r.estado}")
            print(f"    sid    : {r.sid}")
            if r.error:
                print(f"    error  : {r.error}")
            if not r.exito:
                fallos += 1

    print()
    if fallos:
        print("Algunos envios fallaron. Revisa los errores de arriba.")
        return 1
    print("Listo. Revisa tu app — el mensaje deberia llegar en unos segundos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
