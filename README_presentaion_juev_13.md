---
marp: true
theme: gaia
size: 16:9
paginate: true
---

# Sistema de Publicaciones Multi-Plataforma
Automatización de contenido para Redes Sociales
Facultad de Ciencias de la Computación

---

## 📋 Arquitectura del Sistema

El sistema consta de **3 componentes principales**:

1. **Generación de Contenido con IA** (OpenAI GPT-3.5)
2. **Módulos de Publicación** (Facebook, Instagram, WhatsApp)
3. **Orquestador Central** (Flask API)

---

## 🧠 Generación de Contenido con IA (1/3)

```python
def generate_response_ia(question, historial_texto):
    try:
        system_prompt = """
        Eres un asistente para generar publicaciones en:
        instagram, tiktok, whatsapp, facebook, linkedin
        
        Reglas:
        - Usa lenguaje simple, claro y amigable
        - Mantén el contexto según el historial
        - Adapta el tono según la plataforma
        
        Retorna SOLO este formato JSON:
        {
          "instagram": {"response": "texto..."},
          "tiktok": {"response": "texto..."},
          "whatsapp": {"response": "texto..."},
          "facebook": {"response": "texto..."},
          "linkedin": {"response": "texto..."}
        }
        """
```


---

## 🧠 Generación de Contenido con IA (1/3)

```python
def generate_response_ia(question, historial_texto):
    try:
        system_prompt = """
        Eres un asistente para generar publicaciones en:
        instagram, tiktok, whatsapp, facebook, linkedin
        
        Reglas:
        - Usa lenguaje simple, claro y amigable
        - Mapta el tono según la plataforma
        **TU TAREA:**
        1. Analizar la intención del usuario
        2. Determinar si solicita crear publicaciones o es conversación general
        3. Responder en un formato JSON específico

        **TIPOS DE INTERACCIÓN:**

        A) **CONVERSACIÓN GENERAL** (saludos, preguntas, consultas):
        - Ejemplos: "hola", "buenos días", "¿qué puedes hacer?", "ayuda", "gracias"
        - Responde de forma amigable y explica tus capacidades

        B) **SOLICITUD DE PUBLICACIÓN**:
        - Ejemplos: "crea una publicación sobre...", "necesito post para...", "genera contenido sobre..."
        - Crea contenido adaptado para cada plataforma

        **FORMATO DE RESPUESTA (CRÍTICO - SOLO RETORNA ESTE JSON):**

        Para CONVERSACIÓN GENERAL:
        {
            "status": "conversacion",
            "mensaje": "Tu respuesta amigable aquí",
            "haypublicacion": false,
            "publicaciones": {}
        }

        Para SOLICITUD DE PUBLICACIÓN:
        {
            "status": "publicacion",
            "mensaje": "He creado publicaciones personalizadas para cada plataforma. ¿Te gustaría modificar alguna?",
            "haypublicacion": true,
            "publicaciones": {
                "facebook": {
                    "response": "Texto optimizado para Facebook (más extenso, incluye enlaces)"
                },
                "instagram": {
                    "response": "Texto para Instagram (incluye emojis y hashtags relevantes)"
                },
                "linkedin": {
                    "response": "Texto profesional para LinkedIn (tono formal, enfoque académico/profesional)"
                },
                "tiktok": {
                    "response": "Texto corto y dinámico para TikTok (muy visual, hashtags trending)"
                },
                "whatsapp": {
                    "response": "Texto directo para WhatsApp (conversacional, call-to-action claro)"
                }
            }
        }

        """
```

---

## 🧠 Llamada a OpenAI API (2/3)

```python
        user_prompt = f"""
        instrucciones del cliente para la publicacion:
        {question}
        """
        
        # Llamada a OpenAI
        response = client_opneai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=800
        )
```

---

## 🧠 Procesamiento de Respuesta (3/3)

```python
        # Extraer y parsear respuesta
        respuesta_texto = response.choices[0].message.content
        parsed = parse_json_relajado(respuesta_texto)
        
        return parsed
        
    except Exception as e:
        logger.error(f"Error en generate_response_ia: {e}")
        return "Lo siento, ocurrió un error."
```

**Resultado:** Diccionario con 5 publicaciones personalizadas

---

## 📤 Formato de Respuesta IA

```json
{
  "instagram": {
    "response": "Texto optimizado con emojis y hashtags"
  },
  "tiktok": {
    "response": "Texto corto y dinámico"
  },
  "whatsapp": {
    "response": "Mensaje directo y conversacional"
  },
  "facebook": {
    "response": "Texto extenso con enlaces"
  },
  "linkedin": {
    "response": "Contenido profesional y formal"
  }
}
```

---

## 🔷 Módulo 1: Facebook

### Clase `Facebook`

**Variables de entorno requeridas:**
* `FACEBOOK_PAGE_ID`
* `FACEBOOK_PAGE_ACCESS_TOKEN`

**API utilizada:** Graph API v24.0

---

## 🔷 Métodos de Facebook

### `me()` - Información de la página
```python
def me(self):
    fb_url = f"https://graph.facebook.com/v24.0/me"
    resp = requests.get(fb_url, params={"access_token": self.access_token})
    return resp.text, resp.status_code, {'Content-Type': 'application/json'}
```

---

## 🔷 Facebook: Publicar Texto

```python
def publicar_texto(self, message):
    if not message:
        return {"error": "Falta el campo requerido: message"}, 400
    
    fb_url = f"https://graph.facebook.com/v24.0/{self.page_id}/feed"
    payload = {
        "message": message, 
        "access_token": self.access_token
    }
    resp = requests.post(fb_url, data=payload)
    resp_json = resp.json()
```

---

## 🔷 Facebook: Publicar Texto (continuación)

```python
    if "id" not in resp_json:
        logger.error(f"No se pudo publicar: {resp_json}")
        return {"error": "No se pudo publicar el texto"}, 500
    
    return {"publicacion_id": resp_json["id"]}, 200
```

**Resultado:** ID de la publicación creada

---

## 🔷 Facebook: Publicar Imagen

```python
def publicar_imagen(self, caption, image_url):
    if not caption or not image_url:
        return {"error": "Faltan campos requeridos"}, 400
    
    fb_url = f"https://graph.facebook.com/v24.0/{self.page_id}/photos"
    payload = {
        "url": image_url, 
        "caption": caption, 
        "access_token": self.access_token
    }
    resp = requests.post(fb_url, data=payload)
    resp_json = resp.json()
```

---

## 🔷 Facebook: Publicar Imagen (continuación)

```python
    if "id" not in resp_json:
        logger.error(f"Error: {resp_json}")
        return {"error": "No se pudo publicar la imagen"}, 500
    
    return {"publicacion_id": resp_json["id"]}, 200
```

**Endpoint:** `/page_id/photos`
**Resultado:** ID de la foto publicada

---

## 📸 Módulo 2: Instagram

### Clase `Instagram`

**Variables de entorno requeridas:**
* `INSTAGRAM_ACCESS_TOKEN`
* `INSTAGRAM_USER_ID`

**API utilizada:** Instagram Graph API

```python
class Instagram:
    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.user_id = os.getenv("INSTAGRAM_USER_ID")
        
        if not self.access_token or not self.user_id:
            raise ValueError("Faltan variables de entorno de Instagram")
```

---

## 📸 Proceso de Publicación Instagram (1/2)

### Paso 1: Crear contenedor de media

```python
def publicar(self, caption, image_url, reintentos=5, delay=4):
    if not caption or not image_url:
        return {"error": "Faltan campos requeridos"}, 400
    
    # 1️⃣ Crear contenedor de media
    media_url = f"https://graph.instagram.com/{self.user_id}/media"
    payload = {
        "caption": caption, 
        "image_url": image_url, 
        "access_token": self.access_token
    }
    resp = requests.post(media_url, data=payload)
    resp_json = resp.json()
    
    if "id" not in resp_json:
        return {"error": "No se pudo crear el contenedor"}, 500
    
    creation_id = resp_json["id"]
    logger.info(f"Contenedor creado: {creation_id}")
```

---

## 📸 Proceso de Publicación Instagram (2/2)

### Paso 2: Publicar con reintentos

```python
    # 2️⃣ Intentar publicar con reintentos
    publish_url = f"https://graph.instagram.com/{self.user_id}/media_publish"
    
    for intento in range(1, reintentos + 1):
        logger.info(f"Intento {intento} de publicar la media...")
        time.sleep(delay)  # ⏳ Esperar que la imagen se procese
        
        publish_payload = {
            "creation_id": creation_id, 
            "access_token": self.access_token
        }
        publish_resp = requests.post(publish_url, data=publish_payload)
        publish_json = publish_resp.json()
        
        if "id" in publish_json:
            logger.info(f"✅ Publicación exitosa en intento {intento}")
            return {"publicacion_id": publish_json["id"]}, 200
        
        if intento == reintentos:
            return {"error": "No se pudo publicar después de reintentos"}, 500
```

---

## 💬 Módulo 3: WhatsApp

### Clase `WhatsApp`

**Variables de entorno requeridas:**
* `TWILIO_ACCOUNT_SID`
* `TWILIO_AUTH_TOKEN`
* `TWILIO_SANDBOX_NUMBER`

```python
class WhatsApp:
    def __init__(self):
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        sandbox_number = os.getenv('TWILIO_SANDBOX_NUMBER')
        
        if not account_sid or not auth_token or not sandbox_number:
            raise ValueError("Faltan variables de entorno de Twilio")
        
        self.client = Client(account_sid, auth_token)
        self.from_number = f"whatsapp:{sandbox_number}"
```

---

## 💬 WhatsApp: Enviar Mensaje (1/2)

```python
def send_message(self, to_number, message_body):
    try:
        # Validación de campos
        if not to_number or not message_body:
            return jsonify({'error': 'Faltan campos'}), 400
        
        # Agregar prefijo whatsapp: si no lo tiene
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
```

---

## 💬 WhatsApp: Enviar Mensaje (2/2)

```python
        # Enviar mensaje usando Twilio
        message = self.client.messages.create(
            body=message_body,
            from_=self.from_number,
            to=to_number
        )
        
        logger.info(f"Mensaje enviado a {to_number}")
        return message
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
```

---

## 🔄 Flujo Completo del Sistema

1. **Usuario envía instrucción** → Webhook Flask
2. **IA genera contenido** → 5 textos personalizados
3. **Sistema publica en paralelo:**
   * Facebook → `publicar_texto()` o `publicar_imagen()`
   * Instagram → `publicar()` (2 pasos)
   * WhatsApp → `send_message()`
4. **Retorna resultados** → JSON con IDs de publicaciones

---

## 🛡️ Manejo de Errores

**Todas las clases implementan:**

✅ Validación de variables de entorno
✅ Validación de campos requeridos
✅ Logging detallado con `logger`
✅ Respuestas estructuradas (JSON + status code)
✅ Reintentos automáticos (Instagram)

---

## 📊 Ventajas del Sistema

* **Automatización total:** Un comando → 5 publicaciones
* **Contenido adaptado:** IA ajusta tono por plataforma
* **Robusto:** Manejo de errores y reintentos
* **Escalable:** Fácil agregar más redes sociales
* **Trazabilidad:** Logs completos de cada operación

---

## 🔧 Tecnologías Utilizadas

| Componente | Tecnología |
|------------|------------|
| Backend | Python + Flask |
| IA | OpenAI GPT-3.5 Turbo |
| Facebook | Graph API v24.0 |
| Instagram | Instagram Graph API |
| WhatsApp | Twilio API |
| Config | python-dotenv |
| HTTP | requests |

---

## 📝 Ejemplo de Uso

**Input del usuario:**
```
"Crear publicación sobre el retiro de materias"
```

**Output del sistema:**
* ✅ Post en Facebook con enlace
* ✅ Historia en Instagram con hashtags
* ✅ Mensaje WhatsApp a lista de difusión
* ✅ Post profesional en LinkedIn
* ✅ Video corto en TikTok

---

## 🚀 Siguientes Pasos

1. Implementar LinkedIn y TikTok
2. Agregar programación de publicaciones
3. Dashboard de analíticas
4. Sistema de aprobación de contenido
5. Generación de imágenes con DALL-E

---

