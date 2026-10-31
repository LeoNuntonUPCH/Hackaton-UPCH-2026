"""Lista las plantillas de contenido (Content Templates) de tu cuenta Twilio.

    python listar_plantillas.py

Sirve para obtener el ContentSid exacto, sin tener que copiarlo a mano.
"""
import base64
import json
import sys
import urllib.error
import urllib.request

sys.path.insert(0, ".")
from satq import mensajeria  # noqa: E402

cfg = mensajeria.configuracion()
if cfg is None:
    print("No hay credenciales en .env")
    sys.exit(1)

cred = base64.b64encode(f"{cfg.account_sid}:{cfg.auth_token}".encode()).decode()
peticion = urllib.request.Request(
    "https://content.twilio.com/v1/Content?PageSize=50",
    headers={"Authorization": f"Basic {cred}"},
)

try:
    with urllib.request.urlopen(peticion, timeout=15) as resp:
        datos = json.loads(resp.read().decode())
except urllib.error.HTTPError as e:
    print(f"Twilio respondio {e.code}: {e.read().decode()[:300]}")
    sys.exit(1)
except Exception as e:
    print(f"Error de conexion: {e}")
    sys.exit(1)

plantillas = datos.get("contents", [])
if not plantillas:
    print("No se encontraron plantillas en esta cuenta.")
    sys.exit(0)

print(f"{len(plantillas)} plantilla(s) encontrada(s):\n")
for p in plantillas:
    print(f"  nombre : {p.get('friendly_name')}")
    print(f"  SID    : {p.get('sid')}")
    print(f"  idioma : {p.get('language')}")
    tipos = list((p.get("types") or {}).keys())
    print(f"  tipo   : {', '.join(tipos) if tipos else '-'}")
    cuerpo = (p.get("types") or {}).get("twilio/text", {}).get("body")
    if cuerpo:
        print(f"  body   : {cuerpo!r}")
    print()
