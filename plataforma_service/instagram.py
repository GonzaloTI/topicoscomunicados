# instagram.py
import os
import time
import requests
import logging
from flask import jsonify

logger = logging.getLogger(__name__)

class Instagram:
    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.user_id = os.getenv("INSTAGRAM_USER_ID")

        if not self.access_token or not self.user_id:
            raise ValueError("Faltan variables de entorno de Instagram (ACCESS_TOKEN o USER_ID).")

    def publicar(self, caption, image_url, reintentos=5, delay=4):
        """
        Publica una imagen con caption en Instagram, con reintentos si la media no está lista.
        """
        if not caption or not image_url:
            return {"error": "Faltan campos requeridos: caption o image_url"}, 400

        # 1️⃣ Crear contenedor de media
        media_url = f"https://graph.instagram.com/{self.user_id}/media"
        payload = {"caption": caption, "image_url": image_url, "access_token": self.access_token}
        resp = requests.post(media_url, data=payload)
        resp_json = resp.json()

        if "id" not in resp_json:
            logger.error(f"No se pudo crear el contenedor de media: {resp_json}")
            return {"error": "No se pudo crear el contenedor de media", "detalle": resp_json}, 500

        creation_id = resp_json["id"]
        logger.info(f"Contenedor de media creado: {creation_id}")

        # 2️⃣ Intentar publicar con reintentos
        publish_url = f"https://graph.instagram.com/{self.user_id}/media_publish"

        for intento in range(1, reintentos + 1):
            logger.info(f"Intento {intento} de publicar la media...")
            time.sleep(delay)
            publish_payload = {"creation_id": creation_id, "access_token": self.access_token}
            publish_resp = requests.post(publish_url, data=publish_payload)
            publish_json = publish_resp.json()
            logger.debug(f"Respuesta intento {intento}: {publish_json}")

            if "id" in publish_json:
                logger.info(f"Publicación exitosa en intento {intento}")
                return {"publicacion_id": publish_json["id"], "creation_id": creation_id}, 200

            if intento == reintentos:
                logger.error(f"No se pudo publicar después de {reintentos} intentos")
                return {"error": "No se pudo publicar la media después de varios intentos", "detalle": publish_json}, 500
