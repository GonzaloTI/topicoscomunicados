# sender.py
import logging
from plataforma_service.facebook import Facebook
from plataforma_service.instagram import Instagram
from plataforma_service.linkedin import LinkedIn
from plataforma_service.tiktok import TikTok
from plataforma_service.whatsapp import WhatsApp
import re

logger = logging.getLogger(__name__)

class Sender:
    def __init__(self):
        """Instancia los servicios de mensajería de cada plataforma."""
        try:
            self.whatsapp = WhatsApp()
            self.facebook = Facebook()
            self.instagram = Instagram()
            self.linkedin = LinkedIn()
            self.tiktok = TikTok()
            logger.info("Servicios de mensajería inicializados correctamente.")
        except Exception as e:
            logger.error(f"Error al inicializar los servicios: {e}")
            raise
    def _clean_text(self, text: str) -> str:
        # Elimina emojis y caracteres no ASCII
        return re.sub(r'[^\x00-\x7F]+', '', text)

    def send(self, data: dict):
        """
        Formato esperado:
        {
            "facebook": {"response": "..."},
            "instagram": {"response": "..."},
            "linkedin": {"response": "..."},
            "tiktok": {"response": "..."},
            "whatsapp": {"response": "..."}
        }
        """
        # Imprimir datos limpios de emojis
       
        try:
            if not isinstance(data, dict):
                raise ValueError("El parámetro 'data' debe ser un diccionario.")

            results = {}

            # WhatsApp
            if "whatsapp" in data and "response" in data["whatsapp"]:
                message = data["whatsapp"]["response"]
                
                
                message=self.whatsapp.send_message(message_body=message,to_number="whatsapp:+59167769632")
                
                results["whatsapp"] = message.sid
                logger.info("enviado por whatsapp")

            # # Facebook
            if "facebook" in data and "response" in data["facebook"]:
                message = data["facebook"]["response"]
                results["facebook"] = self.facebook.publicar_texto(message)

            # # Instagram
            if "instagram" in data and "response" in data["instagram"]:
                message = data["instagram"]["response"]
                results["instagram"] = self.instagram.publicar(caption=message,image_url="https://mrmoviliano.com/wp-content/uploads/2020/01/jfif.jpg")

            # # LinkedIn
            if "linkedin" in data and "response" in data["linkedin"]:
                message = data["linkedin"]["response"]
                results["linkedin"] = self.linkedin.publicar(message)

            # # TikTok
            if "tiktok" in data and "response" in data["tiktok"]:
                message = data["tiktok"]["response"]
                results["tiktok"] = self.tiktok.publicar_imagen_url( texto=message,imagen_url="https://pagina-de-presentacion3.onrender.com/images/flores.jpg")

            logger.info("Mensajes enviados a todas las plataformas disponibles.")
            return results

        except Exception as e:
            logger.error(f"Error en Sender.send: {e}")
            return {"error": str(e)}
