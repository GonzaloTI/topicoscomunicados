# facebook.py
import os
import requests
import logging

logger = logging.getLogger(__name__)

class Facebook:
    def __init__(self):
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")

        if not self.page_id or not self.access_token:
            raise ValueError("Faltan variables de entorno de Facebook (PAGE_ID o PAGE_ACCESS_TOKEN).")

    def me(self):
        """Retorna el JSON crudo de /me"""
        fb_url = f"https://graph.facebook.com/v24.0/me"
        resp = requests.get(fb_url, params={"access_token": self.access_token})
        return resp.text, resp.status_code, {'Content-Type': 'application/json'}

    def publicar_imagen(self, caption, image_url):
        """Publica imagen con caption en la página"""
        if not caption or not image_url:
            return {"error": "Faltan campos requeridos: caption o image_url"}, 400

        fb_url = f"https://graph.facebook.com/v24.0/{self.page_id}/photos"
        payload = {"url": image_url, "caption": caption, "access_token": self.access_token}
        resp = requests.post(fb_url, data=payload)
        resp_json = resp.json()

        if "id" not in resp_json:
            logger.error(f"No se pudo publicar la imagen: {resp_json}")
            return {"error": "No se pudo publicar la imagen", "detalle": resp_json}, 500

        return {"publicacion_id": resp_json["id"]}, 200

    def publicar_texto(self, message):
        """Publica solo texto en la página"""
        if not message:
            return {"error": "Falta el campo requerido: message"}, 400

        fb_url = f"https://graph.facebook.com/v24.0/{self.page_id}/feed"
        payload = {"message": message, "access_token": self.access_token}
        resp = requests.post(fb_url, data=payload)
        resp_json = resp.json()

        if "id" not in resp_json:
            logger.error(f"No se pudo publicar el texto: {resp_json}")
            return {"error": "No se pudo publicar el texto", "detalle": resp_json}, 500

        return {"publicacion_id": resp_json["id"]}, 200
