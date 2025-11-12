---
marp: true
theme: gaia
---

# Webhook para Conexión con Twilio

Usando Python, Flask y WhatsApp

---

## 📚 Stack de Librerías

Se utilizan las siguientes librerías de Python:
* **openai:** Api key para usar gpt turbo 3.5.
* **Flask:** Servidor web para recibir el webhook.
* **twilio:** Librería oficial para enviar respuestas.
* **python-dotenv:** Gestión de variables de entorno (keys, tokens).
* **psycopg2-binary:** Conexión con PostgreSQL.
* **requests:** Para otras peticiones API.
* **cloudinary:** Opcional para guardar las imagenes generadas.


---

## 💡 Concepto Clave: ¿Qué es una API?

Una **API** (Interfaz de Programación de Aplicaciones) es un **contrato** entre dos programas.

* Es como el **mesero** en un restaurante:
    1.  Tú (la app) le das un pedido (petición).
    2.  El mesero (API) lo lleva a la cocina (el servidor, ej. Twilio).
    3.  El mesero (API) te trae la comida (la respuesta).

* Permite que programas distintos (como nuestra app y LinkedIn) hablen entre sí de forma segura.

---

## 💡 Concepto Clave: ¿Qué es un LLM?

Un **LLM** (Modelo de Lenguaje Grande) es una **Inteligencia Artificial** entrenada para **entender y generar texto**.

* Piensa en él como un "cerebro" que ha leído casi todo Internet.
* **¿Qué hace?**
    * Responde preguntas (ChatGPT).
    * Traduce idiomas.
    * Resume textos largos.
    * Escribe código.
* En este proyecto, se podría usar un LLM para crear respuestas más naturales y humanas para el bot.

---


## 🏛️ Decisión del Stack Tecnológico

La arquitectura principal del proyecto:

* **Backend:**
    * **Python** con el micro-framework **Flask**.
    * (Manejará la lógica de negocio y la conexión con las APIs).

* **Frontend:**
    * **Node.js** (para el entorno de desarrollo y *build* de la interfaz de usuario).



---
## ⚙️ Configuración Clave: Twilio Sandbox

Pasos para configurar el **Twilio Sandbox para WhatsApp**:

1. Registrar un nuevo número con un chip nuevo.
2. Escanear el código QR para vincular el número al Sandbox.

---


## 🤖 Lógica de Respuestas (Ejemplo JSON)

La aplicación puede usar una lógica (como un JSON) para determinar qué responder según la red social o el contexto.

```json
{
    "facebook": {
        "response": "¿Necesitas orientación sobre el retiro de materias? ..."
    },
    "instagram": {
        "response": "¿Necesitas ayuda con el retiro de materias? ..."
    },
    "linkedin": {
        "response": "¿Buscas información sobre el retiro de materias? ..."
    },
    "whatsapp": {
        "response": "¿Tienes dudas sobre el retiro de materias? ¡Escríbenos! 📚✨"
    }
}
```

---


## ⚙️ Restricciones y pasos para LinkedIn

**Restricciones:**

* Perfil verificado: Solo cuentas personales verificadas pueden usar la API.
* Número mínimo de conexiones: 1–2 contactos reales antes de crear páginas.
* Scopes necesarios: `w_member_social` y `r_liteprofile`.
* Roles de administrador: Se requiere ser admin de la página para publicar.
* Limitaciones: Publicaciones automatizadas tienen límites diarios.

**Pasos recomendados:**

1. Verificar correo y completar perfil.
2. Conectar con 1–2 contactos.
3. Crear la página desde desktop y asignar tu cuenta como admin.
4. Crear la app en LinkedIn Developers y asociar permisos.
5. Implementar OAuth2 para generar `access_token` y publicar vía API.

---

## ⚙️ Pasos para la API de TikTok

1. Crear cuenta de desarrollador en **TikTok for Developers**.
2. Crear una App y obtener `Client Key` y `Client Secret`.
3. Configurar los Redirect URIs para OAuth2.
4. Solicitar scopes según la acción (lectura de perfil, publicación de videos, etc.).
5. Implementar el flujo OAuth2: obtener `authorization_code` e intercambiarlo por `access_token`.
6. Usar los endpoints oficiales (`/video/upload/`, `/user/info/`) con `access_token` y `open_id`.

---

## ⚙️ Pasos para la API de Instagram

1. Crear cuenta de desarrollador en Facebook y una App.
2. Asociar tu cuenta de Instagram Business o Creator con la página de Facebook.
3. Obtener Instagram Graph API token con permisos `instagram_basic` y `instagram_content_publish`.
4. Implementar OAuth2 para autorizar la cuenta y obtener `access_token`.
5. Usar los endpoints oficiales (`/me/media`, `/media_publish`) para publicar fotos o videos.
6. Renovar token según los tiempos que indica la API (normalmente cada 60 días).

---

## ⚙️ Pasos para la API de Telegram

1. Crear un Bot con BotFather en Telegram y obtener el token del bot.
2. Configurar un webhook apuntando a tu servidor Flask.
3. Implementar rutas Flask que reciban POST con actualizaciones (`update`).
4. Parsear los mensajes y enviar respuestas con `sendMessage`, `sendPhoto`, etc.
5. Configurar seguridad: validar `secret_token` o IPs de Telegram.
6. Testear localmente con ngrok antes de desplegar en producción.
