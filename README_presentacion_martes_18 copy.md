---
marp: true
theme: gaia
size: 16:9
paginate: true
---

# Sistema de Publicaciones Multi-Plataforma
Automatización de contenido para 5 Redes Sociales
Facultad de Ciencias de la Computación

---

## 📋 Arquitectura del Sistema

El sistema automatiza publicaciones en **5 plataformas**:

1. **Facebook** - Graph API v24.0
2. **Instagram** - Instagram Graph API
3. **WhatsApp** - Twilio API
4. **LinkedIn** - UGC Posts API
5. **TikTok** - TikTok API v2 (Node.js)

Cada módulo maneja autenticación, validación y publicación de forma independiente.

---

## 🧠 Generación de Contenido con IA

```python
def generate_response_ia(question, historial_texto):
    system_prompt = """
    Eres un asistente para generar publicaciones en:
    facebook, instagram, whatsapp, linkedin, tiktok
    
    **FORMATO DE RESPUESTA (CRÍTICO - SOLO RETORNA ESTE JSON):**
    
    Para CONVERSACIÓN GENERAL:
    {
        "status": "conversacion",
        "mensaje": "Tu respuesta amigable aquí",
        "haypublicacion": false,
        "publicaciones": {}
    }
```

---

## 🧠 IA - Formato de Publicaciones

```python
    Para SOLICITUD DE PUBLICACIÓN:
    {
        "status": "publicacion",
        "mensaje": "He creado publicaciones personalizadas...",
        "haypublicacion": true,
        "publicaciones": {
            "facebook": {
                "response": "Texto extenso con enlaces"
            },
            "instagram": {
                "response": "Texto con emojis y hashtags"
            },
            "linkedin": {
                "response": "Texto profesional y formal"
            },
            "tiktok": {
                "response": "Texto corto y dinámico"
            },
            "whatsapp": {
                "response": "Mensaje directo con call-to-action"
            }
        }
    }
    """
```

---

## 🔷 Módulo 1: Facebook - Configuración

```python
class Facebook:
    def __init__(self):
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
        
        if not self.page_id or not self.access_token:
            raise ValueError("Faltan variables de entorno de Facebook")
```

**Variables requeridas:**
- `FACEBOOK_PAGE_ID`
- `FACEBOOK_PAGE_ACCESS_TOKEN`

**API:** Graph API v24.0

---

## 🔷 Facebook - Método `me()`

```python
def me(self):
    """Obtiene información de la página"""
    fb_url = f"https://graph.facebook.com/v24.0/me"
    resp = requests.get(fb_url, params={
        "access_token": self.access_token
    })
    return resp.text, resp.status_code, {
        'Content-Type': 'application/json'
    }
```

**Retorna:** Datos de la página (nombre, ID, categoría)

---

## 🔷 Facebook - Publicar Texto

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
    
    if "id" not in resp_json:
        logger.error(f"No se pudo publicar: {resp_json}")
        return {"error": "No se pudo publicar el texto"}, 500
    
    return {"publicacion_id": resp_json["id"]}, 200
```

---

## 🔷 Facebook - Publicar Imagen

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
    
    if "id" not in resp_json:
        return {"error": "No se pudo publicar la imagen"}, 500
    
    return {"publicacion_id": resp_json["id"]}, 200
```

---

## 📸 Módulo 2: Instagram - Configuración

```python
class Instagram:
    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.user_id = os.getenv("INSTAGRAM_USER_ID")
        
        if not self.access_token or not self.user_id:
            raise ValueError("Faltan variables de entorno de Instagram")
```

**Variables requeridas:**
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_USER_ID`

**API:** Instagram Graph API

---

## 📸 Instagram - Paso 1: Crear Contenedor

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
    logger.info(f"✅ Contenedor creado: {creation_id}")
```

---

## 📸 Instagram - Paso 2: Publicar con Reintentos

```python
    # 2️⃣ Intentar publicar con reintentos
    publish_url = f"https://graph.instagram.com/{self.user_id}/media_publish"
    
    for intento in range(1, reintentos + 1):
        logger.info(f"Intento {intento} de publicar...")
        time.sleep(delay)  # ⏳ Esperar procesamiento de imagen
        
        publish_payload = {
            "creation_id": creation_id, 
            "access_token": self.access_token
        }
        publish_resp = requests.post(publish_url, data=publish_payload)
        publish_json = publish_resp.json()
        
        if "id" in publish_json:
            logger.info(f"✅ Publicación exitosa en intento {intento}")
            return {"publicacion_id": publish_json["id"]}, 200
    
    return {"error": "No se pudo publicar después de reintentos"}, 500
```

---

## 💬 Módulo 3: WhatsApp - Configuración

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

**Variables requeridas:**
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_SANDBOX_NUMBER`

---

## 💬 WhatsApp - Enviar Mensaje

```python
def send_message(self, to_number, message_body):
    try:
        # Validación
        if not to_number or not message_body:
            return jsonify({'error': 'Faltan campos'}), 400
        
        # Agregar prefijo whatsapp: si no lo tiene
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        # Enviar mensaje usando Twilio
        message = self.client.messages.create(
            body=message_body,
            from_=self.from_number,
            to=to_number
        )
        
        logger.info(f"✅ Mensaje enviado a {to_number}")
        return message
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500
```

---

## 💼 Módulo 4: LinkedIn - Configuración

```python
class LinkedIn:
    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.profile_id = os.getenv("LINKEDIN_PROFILE_ID")
        
        if not self.access_token:
            raise ValueError("Falta LINKEDIN_ACCESS_TOKEN")
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Si no hay profile_id, lo obtenemos automáticamente
        if not self.profile_id:
            self.profile_id = self.obtener_profile_id()
```

**Variables requeridas:**
- `LINKEDIN_ACCESS_TOKEN`
- `LINKEDIN_PROFILE_ID` (opcional, se obtiene automáticamente)

---

## 💼 LinkedIn - Obtener Profile ID

```python
def obtener_profile_id(self):
    """Obtiene el 'sub' desde /v2/userinfo"""
    url = "https://api.linkedin.com/v2/userinfo"
    resp = requests.get(url, headers=self.headers)
    
    try:
        data = resp.json()
    except:
        logger.error("No se pudo parsear userinfo")
        return None
    
    logger.info(f"Respuesta userinfo: {data}")
    
    if resp.status_code == 200 and "sub" in data:
        profile_id = data["sub"]
        return profile_id
    
    logger.error(f"No se pudo obtener 'sub': {data}")
    return None
```

---

## 💼 LinkedIn - Publicar Post

```python
def publicar(self, texto):
    if not texto:
        return {"error": "Falta el campo requerido: texto"}, 400
    
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
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
```

---

## 💼 LinkedIn - Respuesta de Publicación

```python
    resp = requests.post(url, json=payload, headers=self.headers)
    resp_json = resp.json()
    
    logger.info(f"Respuesta LinkedIn POST: {resp_json}")
    
    if resp.status_code >= 200 and resp.status_code < 300:
        return {"post_id": resp_json.get("id")}, 200
    
    logger.error(f"Error publicando en LinkedIn: {resp_json}")
    return {
        "error": "No se pudo publicar en LinkedIn", 
        "detalle": resp_json
    }, resp.status_code
```

**API utilizada:** UGC Posts (User Generated Content)

---

## 🎵 Módulo 5: TikTok - Configuración (Node.js)

```javascript
const express = require('express');
const multer = require('multer');
const upload = multer({ dest: 'uploads/' });

const CLIENT_KEY = process.env.TIKTOK_CLIENT_KEY;
const CLIENT_SECRET = process.env.TIKTOK_CLIENT_SECRET;
const REDIRECT_URI = process.env.TIKTOK_REDIRECT_URI;
```

**Variables requeridas:**
- `TIKTOK_CLIENT_KEY`
- `TIKTOK_CLIENT_SECRET`
- `TIKTOK_REDIRECT_URI`

**API:** TikTok API v2
**Lenguaje:** Node.js (Express)

---

## 🎵 TikTok - Verificación de Dominio

```javascript
// Ruta para verificar propiedad del dominio
app.get('/tiktokSTo4Zh8BLznHPQSovtA1HMDm3wsa26Af.txt', (req, res) => {
  res.sendFile(path.join(__dirname, 
    'tiktokSTo4Zh8BLznHPQSovtA1HMDm3wsa26Af.txt'));
});
```

**Propósito:** TikTok verifica que eres dueño del dominio leyendo este archivo específico en tu servidor.

**Ubicación:** Raíz del proyecto
**Acceso:** `https://tudominio.com/tiktokSTo4Zh8BLznHPQSovtA1HMDm3wsa26Af.txt`

---

## 🎵 TikTok - OAuth Callback

```javascript
app.get("/callback", async (req, res) => {
  const code = req.query.code;
  
  if (!code) {
    return res.send("No llegó el code de TikTok.");
  }
  
  try {
    const params = qs.stringify({
      client_key: CLIENT_KEY,
      client_secret: CLIENT_SECRET,
      code,
      grant_type: "authorization_code",
      redirect_uri: REDIRECT_URI,
    });
```

**¿Qué hace?** TikTok redirige aquí después de que el usuario autorice la app.
**Recibe:** `code` en la query string
**Retorna:** `access_token` para hacer llamadas a la API

---

## 🎵 TikTok - Obtener Access Token

```javascript
    const response = await axios.post(
      "https://open.tiktokapis.com/v2/oauth/token/",
      params,
      {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }
    );
    
    const responseData = JSON.stringify(response.data, null, 2);
    res.send(`
      <h2>Respuesta completa de TikTok</h2>
      <pre>${responseData}</pre>

      <h3>Subir video</h3>
      <form action="/uploadVideo" method="POST" 
            enctype="multipart/form-data">
        <input type="hidden" name="access_token" 
               value="${response.data.access_token}">
        <input type="file" name="video" accept="video/*">
        <button type="submit">Subir video a TikTok</button>
      </form>
    `);
```

---

## 🎵 TikTok - Upload Video: Cálculo de Chunks

```javascript
app.post("/uploadVideo", upload.single("video"), async (req, res) => {
  const access_token = req.body.access_token;
  const videoPath = req.file.path;
  const videoStats = fs.statSync(videoPath);
  const videoSize = videoStats.size;

  let chunkSize;
  let totalChunks;
  const CHUNK_BASE_SIZE = 20 * 1024 * 1024; // 20 MiB

  if (videoSize <= 5 * 1024 * 1024) {
    // Video pequeño: 1 chunk
    chunkSize = videoSize;
    totalChunks = 1;
  } else {
    // Video grande: dividir en chunks de 20 MiB
    chunkSize = CHUNK_BASE_SIZE;
    totalChunks = Math.floor(videoSize / chunkSize);
  }

  if (totalChunks === 0 && videoSize > 0) {
    totalChunks = 1;
    chunkSize = videoSize;
  }
```

---

## 🎵 TikTok - Inicializar Subida

```javascript
  // 1️⃣ Inicializar subida en TikTok
  const initResponse = await axios.post(
    "https://open.tiktokapis.com/v2/post/publish/video/init/",
    {
      post_info: {
        title: "Video subido desde mi app Node.js",
        privacy_level: "SELF_ONLY",
        disable_duet: false,
        disable_comment: false,
        disable_stitch: false,
        video_cover_timestamp_ms: 1000
      },
      source_info: {
        source: "FILE_UPLOAD",
        video_size: videoSize,
        chunk_size: chunkSize,
        total_chunk_count: totalChunks
      }
    },
    {
      headers: {
        Authorization: `Bearer ${access_token}`,
        "Content-Type": "application/json; charset=UTF-8",
      },
    }
  );

  const { upload_url, publish_id } = initResponse.data.data;
```

---

## 🎵 TikTok - Subir Chunks Secuencialmente

```javascript
  // 2️⃣ Subir video por chunks con verificación
  const videoBuffer = fs.readFileSync(videoPath);
  const MAX_RETRIES = 3;
  let lastUploadedByte = -1;
  
  for (let i = 0; i < totalChunks; i++) {
    const start = i * chunkSize;
    const end = (i === totalChunks - 1) ? videoSize : (start + chunkSize);
    const chunk = videoBuffer.slice(start, end);

    console.log(`📤 Chunk ${i + 1}/${totalChunks}:`);
    console.log(`   Range: bytes ${start}-${end - 1}/${videoSize}`);
    console.log(`   Size: ${(chunk.length / (1024 * 1024)).toFixed(2)} MB`);

    // Verificar secuencia
    if (lastUploadedByte >= 0 && start !== lastUploadedByte + 1) {
      throw new Error(`ERROR DE SECUENCIA`);
    }
```

---

## 🎵 TikTok - Reintentos por Chunk

```javascript
    let uploadSuccess = false;
    let retryCount = 0;

    while (!uploadSuccess && retryCount < MAX_RETRIES) {
      try {
        const uploadResponse = await axios.put(upload_url, chunk, {
          headers: {
            "Content-Type": "video/mp4",
            "Content-Range": `bytes ${start}-${end - 1}/${videoSize}`,
            "Content-Length": chunk.length
          },
          maxBodyLength: Infinity,
          timeout: 630000, // 6 minutos
          validateStatus: (status) => {
            return status === 206 || status === 201 || status === 200;
          }
        });

        console.log(`✅ Chunk ${i + 1} subido (status: ${uploadResponse.status})`);
        lastUploadedByte = end - 1;
        uploadSuccess = true;

        if (i < totalChunks - 1) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
```

---

## 🎵 TikTok - Manejo de Errores

```javascript
      } catch (chunkError) {
        retryCount++;
        const errorStatus = chunkError.response?.status;
        
        console.error(`❌ Error en chunk ${i + 1} (intento ${retryCount}):`, {
          status: errorStatus,
          statusText: chunkError.response?.statusText,
        });

        // Error 416: servidor rechazó el rango
        if (errorStatus === 416) {
          throw new Error(`El servidor solo recibió hasta anterior chunk`);
        }

        if (retryCount >= MAX_RETRIES) {
          throw new Error(`Chunk ${i + 1} falló después de ${MAX_RETRIES} intentos`);
        }

        // Backoff exponencial
        const waitTime = 2000 * retryCount; // 2s, 4s, 6s
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }
```

---

## 🎵 TikTok - Respuesta Final

```javascript
  console.log(`🎉 ¡Todos los ${totalChunks} chunks subidos exitosamente!`);

  res.send(`
    <h2>✅ Video subido correctamente a TikTok</h2>
    <div style="background: #f0f0f0; padding: 20px;">
      <p><strong>🆔 Publish ID:</strong> ${publish_id}</p>
      <p><strong>📦 Tamaño:</strong> ${(videoSize / (1024 * 1024)).toFixed(2)} MB</p>
      <p><strong>🔢 Chunks:</strong> ${totalChunks}</p>
      <p><strong>📏 Tamaño de chunk:</strong> ${(chunkSize / (1024 * 1024)).toFixed(2)} MB</p>
    </div>
    <p>⏳ Tu video está siendo procesado por TikTok.</p>
  `);
} finally {
  if (fs.existsSync(videoPath)) {
    fs.unlinkSync(videoPath);
  }
}
```

---

## 📊 Comparación de Plataformas

| Plataforma | Lenguaje | Método Principal | Complejidad |
|------------|----------|------------------|-------------|
| Facebook | Python | Graph API POST | ⭐ Baja |
| Instagram | Python | 2 pasos + reintentos | ⭐⭐ Media |
| WhatsApp | Python | Twilio Client | ⭐ Baja |
| LinkedIn | Python | UGC Posts | ⭐⭐ Media |
| TikTok | Node.js | Chunks + OAuth | ⭐⭐⭐ Alta |

---

## 🔄 Flujo de Publicación Integrado

1. **Usuario envía prompt** → "Crear publicación sobre evento X"
2. **IA genera 5 textos** → Personalizados por plataforma
3. **Sistema publica en paralelo:**
   * Facebook: `publicar_texto()` ✅
   * Instagram: `publicar()` con imagen ✅
   * WhatsApp: `send_message()` ✅
   * LinkedIn: `publicar()` profesional ✅
   * TikTok: `uploadVideo()` con chunks ✅
4. **Retorna JSON** con IDs de cada publicación

---

## 🛡️ Características de Seguridad

**Todas las plataformas implementan:**

✅ Validación de variables de entorno
✅ Validación de campos requeridos
✅ Manejo de errores con try-catch
✅ Logging detallado de operaciones
✅ Respuestas estructuradas (JSON + HTTP status)
✅ Reintentos automáticos (Instagram, TikTok)
✅ Limpieza de archivos temporales (TikTok)


---

## 🔧 Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| **Backend Principal** | Python + Flask |
| **Backend TikTok** | Node.js + Express |
| **IA** | OpenAI GPT-3.5 Turbo |
| **Facebook** | Graph API v24.0 |
| **Instagram** | Instagram Graph API |
| **WhatsApp** | Twilio API |
| **LinkedIn** | LinkedIn UGC Posts API v2 |
| **TikTok** | TikTok API v2 |


---


# ¡Gracias!

**Repositorio:** [https://github.com/GonzaloTI/topicoscomunicado.git]
