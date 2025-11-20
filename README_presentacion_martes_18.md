marp: true
theme: gaia
size: 16:9
paginate: true

---

# Sistema de Publicaciones Multi-Plataforma

Automatización de contenido para Redes Sociales
**Plataformas soportadas:** Facebook, Instagram, WhatsApp, LinkedIn, TikTok

---

## 🧠 Generación de Contenido con IA

```python
def generate_response_ia(question, historial_texto):
    system_prompt = """
    Eres un asistente para generar publicaciones en:
    instagram, tiktok, whatsapp, facebook, linkedin
    
    Reglas:
    - Lenguaje simple y amigable
    - Adaptar el tono según la plataforma
    - Responder SOLO en JSON con las 5 plataformas

    Formato de respuesta:
    {
        "facebook": {"response": "..."},
        "instagram": {"response": "..."},
        "linkedin": {"response": "..."},
        "tiktok": {"response": "..."},
        "whatsapp": {"response": "..."}
    }
    """
```

---

## 📤 Formato de Respuesta IA

```json
{
  "facebook": {"response": "Texto extenso con enlaces"},
  "instagram": {"response": "Texto con emojis y hashtags"},
  "linkedin": {"response": "Contenido profesional y formal"},
  "tiktok": {"response": "Texto corto y dinámico, hashtags trending"},
  "whatsapp": {"response": "Mensaje directo y conversacional"}
}
```

---

## 🔷 Facebook

**Clase `Facebook`**
**Variables de entorno:** `FACEBOOK_PAGE_ID`, `FACEBOOK_PAGE_ACCESS_TOKEN`
**API:** Graph API v24.0

```python
def publicar_texto(self, message):
    fb_url = f"https://graph.facebook.com/v24.0/{self.page_id}/feed"
    payload = {"message": message, "access_token": self.access_token}
    resp = requests.post(fb_url, data=payload)
    return resp.json()
```

```python
def publicar_imagen(self, caption, image_url):
    fb_url = f"https://graph.facebook.com/v24.0/{self.page_id}/photos"
    payload = {"url": image_url, "caption": caption, "access_token": self.access_token}
    resp = requests.post(fb_url, data=payload)
    return resp.json()
```

---

## 📸 Instagram

**Clase `Instagram`**
**Variables de entorno:** `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_USER_ID`
**API:** Instagram Graph API

```python
def publicar(self, caption, image_url):
    media_url = f"https://graph.instagram.com/{self.user_id}/media"
    payload = {"caption": caption, "image_url": image_url, "access_token": self.access_token}
    resp = requests.post(media_url, data=payload)
    creation_id = resp.json()["id"]

    publish_url = f"https://graph.instagram.com/{self.user_id}/media_publish"
    publish_payload = {"creation_id": creation_id, "access_token": self.access_token}
    publish_resp = requests.post(publish_url, data=publish_payload)
    return publish_resp.json()
```

---

## 💬 WhatsApp

**Clase `WhatsApp`**
**Variables de entorno:** `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_SANDBOX_NUMBER`

```python
def send_message(self, to_number, message_body):
    if not to_number.startswith('whatsapp:'):
        to_number = f'whatsapp:{to_number}'
    message = self.client.messages.create(body=message_body, from_=self.from_number, to=to_number)
    return message
```

---

## 💼 LinkedIn

**Clase `LinkedIn`**
**Variables de entorno:** `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_PROFILE_ID` (opcional)

```python
def publicar(self, texto):
    url = "https://api.linkedin.com/v2/ugcPosts"
    payload = {
        "author": f"urn:li:person:{self.profile_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": texto},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    resp = requests.post(url, json=payload, headers=self.headers)
    return resp.json()
```

---

## 🎵 TikTok

**Node.js Backend**
**Flujo de publicación:**

1. Verificación de archivo: `/tiktokSTo4Zh8BLznHPQSovtA1HMDm3wsa26Af.txt`
2. Callback OAuth: `/callback?code=XYZ`
3. Inicialización de video: `/v2/post/publish/video/init/`
4. Subida por chunks: `/uploadVideo`
5. Monitoreo de status y eliminación de archivo temporal

```js
app.post("/uploadVideo", upload.single("video"), async (req,res)=>{
  // Leer video, dividir en chunks, enviar PUT a upload_url
});
```
---





---
## 🔄 Flujo Completo del Sistema

1. Usuario envía instrucción → Flask API
2. IA genera contenido → 5 textos personalizados
3. Publicación en paralelo:

   * Facebook → `publicar_texto()` / `publicar_imagen()`
   * Instagram → `publicar()` (2 pasos)
   * WhatsApp → `send_message()`
   * LinkedIn → `publicar()`
   * TikTok → `/uploadVideo`
4. Retorna resultados → JSON con IDs de publicaciones

---

## 📊 Ventajas

* Automatización total: un comando → 5 publicaciones
* Contenido adaptado: IA ajusta tono por plataforma
* Robusto: manejo de errores y reintentos
* Escalable: agregar nuevas redes sociales fácilmente
* Trazabilidad: logs completos

---

## 🚀 Próximos pasos

1. Programación de publicaciones
2. Dashboard de analíticas
3. Sistema de aprobación de contenido
4. Generación de imágenes automáticas (DALL-E)
