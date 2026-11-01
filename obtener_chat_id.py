"""Obtiene el chat_id de quienes escribieron a tu bot de Telegram.

    python obtener_chat_id.py

Requisito: haber puesto TELEGRAM_BOT_TOKEN en el archivo .env, y que cada
persona le haya dado "Start" al bot (un bot no puede escribir primero).

El chat_id es el identificador numérico de cada conversación. Es lo que va
en TELEGRAM_CHAT_IDS, separado por comas.
"""

import json
import sys
import urllib.error
import urllib.request

sys.path.insert(0, ".")
from satq import mensajeria  # noqa: E402

cfg = mensajeria.configuracion_telegram()
if cfg is None:
    print("Falta TELEGRAM_BOT_TOKEN en el archivo .env")
    print()
    print("Pasos:")
    print("  1. En Telegram, escribe a @BotFather y manda /newbot")
    print("  2. Copia el token que te da")
    print("  3. Pegalo en .env como:  TELEGRAM_BOT_TOKEN=...")
    sys.exit(1)

url = f"{cfg.api_base}/bot{cfg.token}/getUpdates"
try:
    with urllib.request.urlopen(url, timeout=15) as resp:
        datos = json.loads(resp.read().decode())
except urllib.error.HTTPError as e:
    cuerpo = e.read().decode()[:300]
    print(f"Telegram respondio {e.code}: {cuerpo}")
    if e.code == 401:
        print("\nEl token parece incorrecto. Revisalo en .env.")
    sys.exit(1)
except Exception as e:
    print(f"Error de conexion: {e}")
    sys.exit(1)

if not datos.get("ok"):
    print(f"Telegram respondio con error: {datos.get('description')}")
    sys.exit(1)

actualizaciones = datos.get("result", [])
if not actualizaciones:
    print("El bot no ha recibido ningun mensaje todavia.")
    print()
    print("Haz esto y vuelve a ejecutar:")
    print("  1. Busca tu bot en Telegram por su @username")
    print("  2. Abrelo y pulsa el boton START (o escribele /hola)")
    print("  3. Que cada companero que deba recibir alertas haga lo mismo")
    sys.exit(0)

# Un mismo chat puede aparecer en varias actualizaciones: nos quedamos con
# uno por chat_id, conservando el nombre mas reciente.
chats = {}
for act in actualizaciones:
    msg = act.get("message") or act.get("edited_message") or {}
    chat = msg.get("chat") or {}
    if chat.get("id") is not None:
        nombre = " ".join(
            x for x in (chat.get("first_name"), chat.get("last_name")) if x
        ) or chat.get("title") or chat.get("username") or "(sin nombre)"
        chats[str(chat["id"])] = nombre

print(f"{len(chats)} conversacion(es) encontrada(s):\n")
for cid, nombre in chats.items():
    print(f"   {nombre:<28} chat_id = {cid}")

print()
print("Copia esta linea a tu archivo .env:")
print()
print(f"TELEGRAM_CHAT_IDS={', '.join(chats.keys())}")
print()
