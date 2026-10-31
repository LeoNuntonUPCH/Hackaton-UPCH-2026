# Activar el envío real por WhatsApp y SMS (Twilio)

Por defecto, SATQ Digital sigue funcionando exactamente como antes: el botón
dice "Simular envío" y no sale ningún mensaje real. Esta guía explica cómo
activar el envío de verdad para la demostración, usando Twilio.

No hace falta instalar nada nuevo. El sistema habla con Twilio directamente
por HTTP (con `urllib`, que viene en Python), así que no hay un paquete
`twilio` que instalar ni que pueda fallar al importar.

---

## 1. Crear la cuenta y encontrar tus credenciales

1. Entra a **[console.twilio.com](https://console.twilio.com)** y crea una
   cuenta (si no tienes una). La cuenta de prueba (trial) es gratis y trae
   saldo inicial, suficiente para la demostración.
2. En el **Dashboard** principal verás dos campos justo debajo del logo:
   - **Account SID** — empieza con `AC...`
   - **Auth Token** — está oculto; haz clic en "View" para revelarlo.
3. Copia ambos valores, los necesitas en el paso 3.

---

## 2. Activar el Sandbox de WhatsApp

Con una cuenta de prueba, Twilio no te deja enviar WhatsApp a cualquier
número todavía: cada destinatario debe "unirse" al Sandbox una vez.

1. En el menú izquierdo: **Messaging → Try it out → Send a WhatsApp message**.
2. Ahí verás un número de Twilio (algo como `+1 415 523 8886`) y un código
   para unirse, tipo `join palabra-clave`.
3. **Desde el celular que vas a usar como destinatario de prueba**, envía por
   WhatsApp ese código (`join palabra-clave`) al número de Twilio.
4. Repite esto con cada número que quieras usar en la demo (tu celular, el
   de un compañero). La unión dura unos días; si expira, se repite el mismo
   paso.

Para SMS no hace falta este paso — un número de Twilio puede enviar SMS a
cualquier número desde el principio (con cuenta trial, a números verificados
en **Phone Numbers → Manage → Verified Caller IDs**, un paso rápido aparte).

---

## 3. Crear el archivo `.env`

En la carpeta del proyecto (`Hackaton-UPCH-2026`), copia `.env.example` a un
archivo nuevo llamado `.env` y rellénalo con tus datos:

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=tu_auth_token_aquí
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_SMS_FROM=+15005550006
TWILIO_DESTINATARIOS_PRUEBA=+51987654321, +51911111111
```

- `TWILIO_WHATSAPP_FROM` es el número del Sandbox del paso 2, con el
  prefijo `whatsapp:` delante.
- `TWILIO_SMS_FROM` es tu número de Twilio normal, sin prefijo (lo
  encuentras en **Phone Numbers → Manage → Active numbers**).
- `TWILIO_DESTINATARIOS_PRUEBA` son los números reales a los que SÍ quieres
  que lleguen los mensajes: el tuyo, el de un compañero. Para WhatsApp,
  deben haberse unido al Sandbox (paso 2). En formato internacional, con
  `+` y separados por coma.

**El archivo `.env` nunca se sube a GitHub** — ya está en `.gitignore`. Si lo
compartes con tu equipo, hazlo por un canal privado (WhatsApp, no un commit).

---

## 4. Probarlo

Arranca el sistema como siempre (`iniciar.bat`, o `python servidor_demo.py`,
o `python -m uvicorn app:app --port 8000`) y entra a **Notificaciones**.

- Si todo está bien configurado, verás arriba a la derecha:
  **"Twilio conectado · envía de verdad a N número(s) de prueba"**, en
  verde, en vez de "Solo simulación".
- Los recuadros de WhatsApp y SMS dirán "conectado · <tu número>" en vez de
  "no conectado".
- El botón dirá **"Enviar de verdad"** en vez de "Simular envío".

Pulsa el botón, confirma en la pantalla siguiente, y revisa el celular del
destinatario de prueba: debería llegar el mensaje en segundos.

En la tabla **Historial de comunicaciones**, la columna **Entrega real**
mostrará el resultado tal como lo devolvió Twilio (entregado, o el motivo
del fallo si algo salió mal), en vez de "No disponible".

---

## 5. Si algo falla

El sistema nunca se cae por esto: si Twilio rechaza el envío (credenciales
mal copiadas, número no unido al Sandbox, sin saldo), el registro queda
marcado como fallido con el motivo exacto que dio Twilio, visible en
"Entrega real". El resto de la aplicación sigue funcionando con normalidad.

Errores típicos:

| Lo que ves en "Entrega real" | Qué significa | Qué hacer |
|---|---|---|
| `recipient has not joined the sandbox` | El número no envió el `join ...` por WhatsApp | Repite el paso 2 con ese número |
| `Authenticate` o `authenticated` | El Account SID o el Auth Token están mal copiados | Revisa el `.env` contra el Dashboard de Twilio |
| `Sin conexión a Twilio` | No hay internet, o un firewall bloquea `api.twilio.com` | Prueba desde otra red |
| `The number ... is not a valid phone number` | Falta el `+` o el código de país en el destinatario | Usa formato internacional: `+51...` |

---

## 6. Volver al modo simulado

Para la auditoría puedes dejarlo apagado sin tocar nada: simplemente no
crees el archivo `.env`, o bórralo si ya lo creaste. El sistema vuelve
exactamente al comportamiento de siempre, sin ningún cambio de código.
