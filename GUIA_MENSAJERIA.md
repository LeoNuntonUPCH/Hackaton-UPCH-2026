# Activar el envío real de notificaciones

Por defecto, SATQ Digital funciona en modo simulado: el botón dice "Simular
envío" y no sale ningún mensaje. Esta guía explica cómo activar el envío de
verdad.

No hace falta instalar nada: el sistema habla con las APIs directamente por
HTTP usando `urllib`, que viene con Python.

Hay tres proveedores soportados. **Telegram es el recomendado** para la
demostración, por la razón que se explica abajo.

---

## Qué se intentó y por qué Telegram

El proyecto plantea avisos por WhatsApp y SMS. Al implementarlo aparecieron
barreras que conviene documentar, para que nadie repita el camino:

**Twilio.** WhatsApp exige, desde abril de 2025, que todo mensaje *iniciado
por la empresa* use una plantilla pre-aprobada. Esas plantillas se gestionan
con la Content API de Twilio, que **no está disponible en cuentas de prueba**
(`20003 — This feature is not available on a Trial account`). Para SMS hace
falta un número propio y saldo, que una cuenta trial recién creada no tiene.

**Meta WhatsApp Cloud API.** Es gratis y sí permite enviar sin cuenta de
pago, pero el alta exige verificar la cuenta de desarrollador por SMS, y
ese SMS no llega de forma fiable a números peruanos.

**Telegram.** No pide verificación de empresa, ni tarjeta, ni saldo: basta
crear un bot. Es el canal que quedó operativo.

Que el canal sea Telegram y no WhatsApp es una decisión de proveedor, no de
arquitectura: el sistema envía por cualquiera de los tres según lo que haya
configurado en `.env`, sin cambiar una línea de código.

---

## Opción A — Telegram (recomendada)

### 1. Crear el bot

1. En Telegram, busca **@BotFather** (el oficial, con check azul).
2. Escríbele `/newbot`.
3. Nombre del bot: por ejemplo `SATQ Digital Alertas`.
4. Username: debe terminar en `bot`, por ejemplo `satq_alertas_bot`.
5. BotFather responde con un **token** así:
   `8123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### 2. Que cada destinatario active la conversación

Un bot de Telegram **no puede escribir primero**. Cada persona que deba
recibir avisos tiene que abrir el bot por su `@username` y pulsar **START**
una vez. A diferencia de WhatsApp, ese permiso no caduca.

### 3. Obtener los chat_id

Pon el token en `.env`:

```
TELEGRAM_BOT_TOKEN=8123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Y ejecuta:

```
python obtener_chat_id.py
```

El script lista a quienes escribieron al bot y te da la línea lista para
copiar:

```
TELEGRAM_CHAT_IDS=123456789, 987654321
```

El `chat_id` es un identificador numérico de la conversación, no un número
de teléfono.

### 4. Probar

```
python probar_whatsapp.py
```

(El script detecta el canal configurado; el nombre quedó del intento inicial
con WhatsApp.)

---

## Opción B — Meta WhatsApp Cloud API



### 1. Crear la app

1. Entra a <https://developers.facebook.com> e inicia sesión con tu cuenta de
   Facebook.
2. **My Apps → Create App**. Elige el caso de uso **Business** (o "Otro" si
   te lo pide) y ponle un nombre, por ejemplo `SATQ Digital`.
3. Dentro de la app, busca el producto **WhatsApp** y pulsa **Set up**.
4. Te pedirá asociar o crear una **cuenta de WhatsApp Business**. Acepta la
   que te ofrece por defecto; no requiere verificación de empresa para el
   modo de prueba.

### 2. Obtener los datos

En el menú lateral: **WhatsApp → API Setup**. Ahí verás todo lo necesario:

| Dato en el panel | Variable del `.env` |
|---|---|
| Temporary access token | `META_WHATSAPP_TOKEN` |
| Phone number ID | `META_WHATSAPP_PHONE_ID` |
| La versión que aparece en el ejemplo de código (`v21.0`, `v23.0`, …) | `META_WHATSAPP_VERSION` |

Ojo con **Phone number ID**: es el identificador numérico largo que muestra
el panel, no el número de teléfono.

El token temporal **caduca en 24 horas**. Para la demostración alcanza; si
necesitas uno permanente, ver la sección "Token permanente" más abajo.

### 3. Registrar los destinatarios

En la misma pantalla, en **To**, hay un desplegable con
**Manage phone number list** (o "Add recipient"). Agrega ahí los celulares
que recibirán los avisos de prueba — hasta 5. Cada número recibe un código
por WhatsApp que hay que confirmar una vez.

Sin este paso, Meta rechaza el envío con
*"Recipient phone number not in allowed list"*.

### 4. Crear el `.env`

En la carpeta del proyecto, copia `.env.example` a `.env` y rellena:

```
META_WHATSAPP_TOKEN=EAAxxxxxxxxxx...
META_WHATSAPP_PHONE_ID=123456789012345
META_WHATSAPP_VERSION=v21.0
TWILIO_DESTINATARIOS_PRUEBA=+51963227613
```

(La variable de destinatarios conserva el prefijo `TWILIO_` por
compatibilidad; sirve para ambos proveedores.)

### 5. Probar

```
python probar_whatsapp.py
```

Debe imprimir `éxito : True` y el mensaje llegar en segundos.

### 6. La ventana de 24 horas

Meta cobra, y a veces bloquea, los mensajes que **inicia la empresa** fuera
de una ventana de servicio. Esa ventana se abre cuando la persona escribe
primero al número de prueba y dura 24 horas; dentro de ella, el texto libre
es gratis.

Para la demostración: pide a cada destinatario que mande cualquier mensaje
("hola") al número de prueba de Meta antes de la presentación. Con eso la
ventana queda abierta y los envíos funcionan sin plantilla.

### Token permanente (opcional)

El token temporal muere a las 24 h. Para uno que dure:

1. **Business Settings → Users → System Users → Add**, crea un usuario de
   sistema con rol Admin.
2. **Generate New Token**, elige tu app y marca los permisos
   `whatsapp_business_messaging` y `whatsapp_business_management`.
3. Copia ese token a `META_WHATSAPP_TOKEN`.

---

## Opción C — Twilio (requiere cuenta de pago)

Se mantiene implementada por si el proyecto adquiere una cuenta de pago.

1. En <https://console.twilio.com>, copia **Account SID** y **Auth Token**.
2. Activa el Sandbox: **Messaging → Try it out → Send a WhatsApp message**.
   Cada destinatario envía el código `join <palabra>` al número indicado.
3. Para WhatsApp hace falta además una plantilla aprobada
   (**Content Template Builder**), que exige cuenta de pago y un WhatsApp
   Sender verificado.
4. Para SMS hace falta un número propio (**Phone Numbers → Buy a number**) y
   saldo.

Variables: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`,
`TWILIO_SMS_FROM`, `TWILIO_WHATSAPP_CONTENT_SID`.

Prioridad: si hay varios configurados, WhatsApp sale por Meta antes que
por Twilio. SMS siempre por Twilio, que es quien provee números. Telegram
va por su propio bot. Los canales conviven sin estorbarse.

---

## Herramientas de apoyo

| Script | Para qué sirve |
|---|---|
| `python probar_whatsapp.py` | Envía un mensaje de prueba y muestra el resultado |
| `python diagnostico_twilio.py` | Revisa saldo, números y tipo de cuenta en Twilio |
| `python listar_plantillas.py` | Lista las plantillas de Twilio (requiere cuenta de pago) |
| `python obtener_chat_id.py` | Lista los chat_id de quienes escribieron al bot de Telegram |

---

## Si algo falla

El sistema nunca se cae por esto: si el envío es rechazado, el registro queda
marcado como fallido con el motivo exacto del proveedor, visible en la
columna **Entrega real** de la pantalla de Notificaciones.

| Mensaje de error | Qué significa | Qué hacer |
|---|---|---|
| `Recipient phone number not in allowed list` | El número no está registrado en Meta | Añádelo en **API Setup → Manage phone number list** |
| `Invalid OAuth access token` | El token de Meta caducó (dura 24 h) | Genera uno nuevo en el panel, o crea un token permanente |
| `ContentSid Required` (Twilio) | WhatsApp exige plantilla para mensajes iniciados por la empresa | Usa Meta, o una cuenta Twilio de pago |
| `This feature is not available on a Trial account` | La Content API de Twilio exige cuenta de pago | Usa Meta |
| `chat not found` (Telegram) | El chat_id es incorrecto, o la persona nunca pulsó START | Ejecuta `python obtener_chat_id.py` |
| `Unauthorized` (Telegram) | El token del bot está mal copiado | Revísalo con @BotFather (`/mybots`) |
| `Sin conexión` | Sin internet, o un firewall bloquea el proveedor | Prueba desde otra red |

---

## Volver al modo simulado

Borra el archivo `.env`, o renómbralo a `.env.inactivo`. El sistema vuelve al
comportamiento de siempre sin tocar una línea de código.
