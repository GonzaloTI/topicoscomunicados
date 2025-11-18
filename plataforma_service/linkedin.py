# linkedin.py
import os
import requests
import logging

logger = logging.getLogger(__name__)

class LinkedIn:
    def __init__(self):
        self.access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        self.profile_id = os.getenv("LINKEDIN_PROFILE_ID")  # opcional, si no existe se consulta

        if not self.access_token:
            raise ValueError("Falta la variable de entorno LINKEDIN_ACCESS_TOKEN.")

        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Si no tenemos profile_id, lo buscamos automáticamente
        if not self.profile_id:
            logger.info("No se encontró LINKEDIN_PROFILE_ID, consultando /userinfo ...")
            self.profile_id = self.obtener_profile_id()

            if not self.profile_id:
                raise ValueError("No se pudo obtener el profile_id desde LinkedIn (/userinfo).")

    def obtener_profile_id(self):
        """
        Obtiene el 'sub' desde https://api.linkedin.com/v2/userinfo
        """
        url = "https://api.linkedin.com/v2/userinfo"
        resp = requests.get(url, headers=self.headers)

        try:
            data = resp.json()
        except:
            logger.error("No se pudo parsear la respuesta de userinfo.")
            return None

        logger.info(f"Respuesta userinfo: {data}")

        if resp.status_code == 200 and "sub" in data:
            profile_id = data["sub"]

            # OPCIONAL: si deseas guardarlo como variable de entorno al vuelo:
            # os.environ["LINKEDIN_PROFILE_ID"] = profile_id

            return profile_id

        logger.error(f"No se pudo obtener el 'sub' desde LinkedIn: {data}")
        return None

    def publicar(self, texto):
        """
        Publica un post de texto en LinkedIn usando UGC Posts.
        """
        if not texto:
            return {"error": "Falta el campo requerido: texto"}, 400

        url = "https://api.linkedin.com/v2/ugcPosts"

        payload = {
            "author": f"urn:li:person:{self.profile_id}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {
                        "text": texto
                    },
                    "shareMediaCategory": "NONE"
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

        resp = requests.post(url, json=payload, headers=self.headers)
        resp_json = resp.json()

        logger.info(f"Respuesta LinkedIn POST: {resp_json}")

        if resp.status_code >= 200 and resp.status_code < 300:
            return {"post_id": resp_json.get("id")}, 200

        logger.error(f"Error publicando en LinkedIn: {resp_json}")
        return {"error": "No se pudo publicar en LinkedIn", "detalle": resp_json}, resp.status_code
