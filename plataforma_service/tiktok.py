# tiktok.py
import os
import time
import logging
import requests

logger = logging.getLogger(__name__)

class TikTok:
    def __init__(self):
        """
        Inicializa el cliente TikTok con manejo automático de tokens.
        """
        self.client_key = os.getenv("CLIENT_KEY")
        self.client_secret = os.getenv("CLIENT_SECRET")

        self.access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
        self.refresh_token_value = os.getenv("TIKTOK_REFRESH_TOKEN")

        # Validar que el access token funciona
        if not self._validar_access_token():
            logger.warning("Access token vencido. Renovando…")
            #sino hacer un refresh al token
            self.refresh_token()

        self.CHUNK_BASE_SIZE = 20 * 1024 * 1024  # 20 MB
        self.MAX_RETRIES = 3

    # ============================================================
    # VALIDAR ACCESS TOKEN
    # ============================================================
    def _validar_access_token(self):
        """
        Hace una prueba simple para verificar si el access_token sigue vivo.
        """
        if not self.access_token or self.access_token == "None":
            return False

        url = "https://open.tiktokapis.com/v2/user/info/?fields=open_id"

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        resp = requests.get(url, headers=headers)
        return resp.status_code == 200

    # ============================================================
    # REFRESCAR TOKEN
    # ============================================================
    def refresh_token(self):
        """
        Usa el refresh_token para obtener un nuevo access_token.
        """
        url = "https://open.tiktokapis.com/v2/oauth/token/"

        payload = {
            "grant_type": "refresh_token",
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token_value
        }

        resp = requests.post(url, data=payload)
        data = resp.json()

        logger.info(f"REFRESH RESPONSE: {data}")

        if "access_token" not in data:
            raise ValueError(f"No se pudo refrescar el token: {data}")

        # Guardar nuevos tokens
        new_access = data["access_token"]
        new_refresh = data.get("refresh_token", self.refresh_token_value)

        self.access_token = new_access
        self.refresh_token_value = new_refresh

        # Guardar en variables de entorno vivas
        os.environ["TIKTOK_ACCESS_TOKEN"] = new_access
        os.environ["TIKTOK_REFRESH_TOKEN"] = new_refresh

        logger.info("Tokens TikTok actualizados correctamente")

        return True

    # ============================================================
    # PUBLICAR VIDEO COMPLETO
    # ============================================================
    def publicar(self, video_path: str):
        """
        Publica un video en TikTok (maneja chunks, init y publish).
        """
        if not os.path.exists(video_path):
            return {"error": "El archivo no existe"}, 400

        video_size = os.path.getsize(video_path)

        # Revalidar token antes de subir
        if not self._validar_access_token():
            logger.info("Token vencido antes de publicar, refrescando…")
            self.refresh_token()

        chunk_size, total_chunks = self._calcular_chunks(video_size)

        logger.info(f"Tamaño video: {video_size} bytes")
        logger.info(f"Chunks: {total_chunks}, tamaño: {chunk_size}")

        init = self._init_upload(video_size, chunk_size, total_chunks)
        if "error" in init:
            return init, 500

        upload_url = init["upload_url"]
        publish_id = init["publish_id"]

        logger.info(f"INIT OK — Publish ID: {publish_id}")

        subida = self._subir_chunks(video_path, upload_url, video_size, chunk_size, total_chunks)

        if subida is not True:
            return subida, 500

        return {
            "mensaje": "Video subido correctamente",
            "publish_id": publish_id,
            "video_size_mb": round(video_size / 1024 / 1024, 2),
            "chunks": total_chunks
        }, 200

    # ============================================================
    # CÁLCULO DE CHUNKS
    # ============================================================
    def _calcular_chunks(self, video_size: int):
        if video_size <= 5 * 1024 * 1024:
            return video_size, 1

        chunk_size = self.CHUNK_BASE_SIZE
        total_chunks = video_size // chunk_size

        if total_chunks == 0:
            total_chunks = 1
            chunk_size = video_size

        return chunk_size, total_chunks

    # ============================================================
    # INIT
    # ============================================================
    def _init_upload(self, video_size, chunk_size, total_chunks):
        url = "https://open.tiktokapis.com/v2/post/publish/video/init/"

        payload = {
            "post_info": {
                "title": "Video desde API Python",
                "privacy_level": "SELF_ONLY"
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunks
            }
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

        resp = requests.post(url, json=payload, headers=headers)
        data = resp.json()

        if "data" not in data:
            logger.error(f"Error INIT: {data}")
            return {"error": "No se pudo inicializar upload", "detalle": data}

        return {
            "upload_url": data["data"]["upload_url"],
            "publish_id": data["data"]["publish_id"]
        }

    # ============================================================
    # SUBIR CHUNKS
    # ============================================================
    def _subir_chunks(self, video_path, upload_url, video_size, chunk_size, total_chunks):
        with open(video_path, "rb") as f:
            for i in range(total_chunks):

                start = i * chunk_size
                end = video_size if i == total_chunks - 1 else start + chunk_size

                f.seek(start)
                chunk = f.read(end - start)

                logger.info(f"📤 Subiendo chunk {i+1}/{total_chunks} → {start}-{end-1}")

                retries = 0
                success = False

                while not success and retries < self.MAX_RETRIES:
                    try:
                        headers = {
                            "Content-Type": "video/mp4",
                            "Content-Range": f"bytes {start}-{end-1}/{video_size}",
                            "Content-Length": str(len(chunk))
                        }

                        r = requests.put(upload_url, headers=headers, data=chunk, timeout=600)

                        if r.status_code in [200, 201, 206]:
                            logger.info(f"Chunk {i+1}/{total_chunks} OK")
                            success = True
                            time.sleep(0.5)

                        else:
                            raise Exception(f"Estado inesperado: {r.status_code}")

                    except Exception as e:
                        retries += 1
                        logger.warning(f"Error chunk {i+1}, intento {retries}: {e}")

                        if retries >= self.MAX_RETRIES:
                            return {"error": f"Falló chunk {i+1}", "detalle": str(e)}

                        wait = 2 * retries
                        logger.info(f"Reintentando en {wait}s…")
                        time.sleep(wait)

        return True

    def publicar_imagen_url(self, imagen_url: str, texto: str):
        """
        Descarga y sube imagen directamente con FILE_UPLOAD (sin necesidad de verificar dominio)
        """
        import tempfile
        
        if not self._validar_access_token():
            logger.info("Token expirado, refrescando…")
            self.refresh_token()
        
        tmp_image_path = None
        
        try:
            # 1️⃣ Descargar imagen
            logger.info(f"Descargando imagen desde: {imagen_url}")
            resp_img = requests.get(imagen_url, stream=True, timeout=30)
            
            if resp_img.status_code != 200:
                return {
                    "error": "No se pudo descargar la imagen", 
                    "detalle": resp_img.text
                }, 400
            
            # Guardar temporalmente
            suffix = os.path.splitext(imagen_url)[-1] or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                for chunk in resp_img.iter_content(1024):
                    tmp_file.write(chunk)
                tmp_image_path = tmp_file.name
            
            file_size = os.path.getsize(tmp_image_path)
            logger.info(f"Imagen descargada: {tmp_image_path} ({file_size} bytes)")
            
            # 2️⃣ INIT - Solicitar upload_url
            init_url = "https://open.tiktokapis.com/v2/post/publish/content/init/"
            
            init_payload = {
                "post_info": {
                    "title": texto,
                    "description": texto,
                    "disable_comment": False,
                    "privacy_level": "SELF_ONLY",
                    "auto_add_music": True
                },
                "source_info": {
                    "source": "FILE_UPLOAD",
                    "photo_images": [
                        {
                            "file_size": file_size
                        }
                    ]
                },
                "post_mode": "DIRECT_POST",
                "media_type": "PHOTO"
            }
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }
            
            logger.info("Solicitando upload_url...")
            init_resp = requests.post(init_url, json=init_payload, headers=headers)
            init_data = init_resp.json()
            
            logger.info(f"INIT Response: {init_data}")
            
            # Validar respuesta INIT
            if init_data.get("error", {}).get("code") != "ok":
                return {
                    "error": "Error en INIT", 
                    "detalle": init_data
                }, 400
            
            # Verificar que existe upload_url
            if "data" not in init_data or "photo_upload_urls" not in init_data["data"]:
                return {
                    "error": "No se recibió upload_url",
                    "detalle": init_data
                }, 400
            
            # 3️⃣ UPLOAD - Subir imagen al servidor de TikTok
            upload_url = init_data["data"]["photo_upload_urls"][0]
            publish_id = init_data["data"]["publish_id"]
            
            logger.info(f"Subiendo imagen a TikTok (publish_id: {publish_id})...")
            
            with open(tmp_image_path, 'rb') as img_file:
                upload_headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "image/jpeg",
                    "Content-Length": str(file_size)
                }
                
                upload_resp = requests.put(
                    upload_url, 
                    data=img_file, 
                    headers=upload_headers,
                    timeout=60
                )
                
                logger.info(f"UPLOAD Status: {upload_resp.status_code}")
                
                if upload_resp.status_code not in [200, 201]:
                    return {
                        "error": "Error al subir imagen", 
                        "detalle": upload_resp.text,
                        "status_code": upload_resp.status_code
                    }, 400
            
            logger.info("✅ Imagen publicada exitosamente")
            
            return {
                "mensaje": "Imagen publicada correctamente",
                "publish_id": publish_id,
                "status": "success"
            }, 200
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de red: {str(e)}")
            return {"error": "Error de conexión", "detalle": str(e)}, 500
            
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return {"error": "Error interno", "detalle": str(e)}, 500
            
        finally:
            # Limpiar archivo temporal
            if tmp_image_path and os.path.exists(tmp_image_path):
                try:
                    os.remove(tmp_image_path)
                    logger.info(f"Archivo temporal eliminado: {tmp_image_path}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar archivo temporal: {e}")



    def publicar_imagen_url_very(self, imagen_url: str, texto: str):
        """
        Publica una imagen en TikTok usando PULL_FROM_URL con DIRECT_POST.
        """
        if not self._validar_access_token():
            logger.info("Token expirado, refrescando…")
            self.refresh_token()

        url = "https://open.tiktokapis.com/v2/post/publish/content/init/"

        payload = {
            "post_info": {
                "title": texto,
                "description": texto,
                "disable_comment": False,
                "privacy_level": "SELF_ONLY",
                "auto_add_music": True
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_cover_index": 0,
                "photo_images": [imagen_url]   # UNA sola imagen
            },
            "post_mode": "DIRECT_POST",
            "media_type": "PHOTO"
        }

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

        resp = requests.post(url, json=payload, headers=headers)
        data = resp.json()

        logger.info(f"POST IMAGEN RESPONSE: {data}")

        if "data" not in data or data.get("error", {}).get("code") != "ok":
            return {"error": "No se pudo publicar la imagen", "detalle": data}, 400

        return {
            "mensaje": "Imagen enviada correctamente",
            "publish_id": data["data"]["publish_id"]
        }, 200



