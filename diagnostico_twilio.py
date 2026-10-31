"""Revisa que recursos tiene disponible tu cuenta Twilio."""
import base64, json, sys, urllib.error, urllib.request
sys.path.insert(0, ".")
from satq import mensajeria  # noqa: E402

cfg = mensajeria.configuracion()
if cfg is None:
    print("No hay credenciales en .env"); sys.exit(1)

cred = base64.b64encode(f"{cfg.account_sid}:{cfg.auth_token}".encode()).decode()

def consultar(url, etiqueta):
    try:
        req = urllib.request.Request(url, headers={"Authorization": f"Basic {cred}"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode()[:200]
        print(f"{etiqueta}: HTTP {e.code} -> {cuerpo}\n")
        return None
    except Exception as e:
        print(f"{etiqueta}: error {e}\n"); return None

base = f"https://api.twilio.com/2010-04-01/Accounts/{cfg.account_sid}"

print("=" * 55)
print("  Diagnostico de la cuenta Twilio")
print("=" * 55)

d = consultar(f"{base}/Balance.json", "Saldo")
if d: print(f"\nSaldo disponible : {d.get('balance')} {d.get('currency')}")

d = consultar(f"{base}.json", "Cuenta")
if d: print(f"Tipo de cuenta   : {d.get('type')}  (status: {d.get('status')})")

d = consultar(f"{base}/IncomingPhoneNumbers.json", "Numeros")
if d:
    nums = d.get("incoming_phone_numbers", [])
    print(f"\nNumeros Twilio   : {len(nums)}")
    for n in nums:
        cap = n.get("capabilities", {})
        print(f"   {n.get('phone_number')}  SMS={cap.get('sms')}  voz={cap.get('voice')}")
    if not nums:
        print("   (ninguno: hay que conseguir uno para enviar SMS)")

d = consultar(f"{base}/OutgoingCallerIds.json", "Verificados")
if d:
    vs = d.get("outgoing_caller_ids", [])
    print(f"\nNumeros verificados (destinos permitidos en trial): {len(vs)}")
    for v in vs:
        print(f"   {v.get('phone_number')}")
print()
