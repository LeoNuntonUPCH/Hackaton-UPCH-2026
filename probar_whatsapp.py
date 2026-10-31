"""Prueba rápida: envía un WhatsApp real usando las credenciales de .env.

    python probar_whatsapp.py
"""
import sys

sys.path.insert(0, ".")
from satq import mensajeria  # noqa: E402

cfg = mensajeria.configuracion()
if cfg is None:
    print("No se encontraron credenciales en .env. Revisa que el archivo exista")
    print("en esta misma carpeta y tenga TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN.")
    sys.exit(1)

destinos = mensajeria.destinatarios_prueba()
if not destinos:
    print("TWILIO_DESTINATARIOS_PRUEBA está vacío en .env.")
    sys.exit(1)

print(f"Enviando WhatsApp de prueba a {destinos[0]} ...")
r = mensajeria.enviar_whatsapp(
    destinos[0],
    "SATQ Digital: mensaje de prueba. Si lees esto, la conexión con Twilio funciona.",
)

print()
print("éxito  :", r.exito)
print("estado :", r.estado)
print("sid    :", r.sid)
print("error  :", r.error)

if r.exito:
    print("\n✅ Revisa tu WhatsApp — el mensaje debería llegar en unos segundos.")
else:
    print("\n❌ No se pudo enviar. Revisa el error de arriba.")
