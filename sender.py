# sender.py
import logging
from plataforma_service.facebook import Facebook
from plataforma_service.imagen_generator import ImageGenerator
from plataforma_service.instagram import Instagram
from plataforma_service.linkedin import LinkedIn
from plataforma_service.tiktok import TikTok
from plataforma_service.video_generator import VideoGenerator
from plataforma_service.whatsapp import WhatsApp
import re

from plataforma_service.whatsappwhapi import WhatsAppWhapi

logger = logging.getLogger(__name__)

class Sender:
    def __init__(self):
        """Instancia los servicios de mensajería de cada plataforma."""
        try:
            self.whatsapp = WhatsApp()
            self.whatsappwhapi = WhatsAppWhapi()
            self.facebook = Facebook()
            self.instagram = Instagram()
            self.linkedin = LinkedIn()
            self.tiktok = TikTok()
            self.imagen_generator = ImageGenerator()
            self.video_generator = VideoGenerator()
            
            
            logger.info("Servicios de mensajería inicializados correctamente.")
        except Exception as e:
            logger.error(f"Error al inicializar los servicios: {e}")
            raise
        
        self.platform_urls = {
                "facebook": "https://www.facebook.com/profile.php?id=61583591706597",
                "instagram": "https://www.instagram.com/kogamii17/",
                "linkedin": "https://www.linkedin.com/in/gonzalo-tarqui-ignacio-334087336/",
                "tiktok": "https://www.tiktok.com/@tiktok_grupo_ficct?lang=es-419"
            }
        
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
            
            
            # ===================== IMAGEN =====================
            # if "instagram" in data and "response" in data["instagram"]:
            #     prompt_imagen = data["instagram"]["response"]
            
            # if prompt_imagen:
            #     try:
            #         imagen_result = self.imagen_generator.generate_image(
            #             prompt_text=prompt_imagen
            #         )
            #         # print("URL Runway:", imagen_result["runway_url"])
            #         # print("URL pública API:", imagen_result["public_url"])
                    
            #         imagen_local_path=imagen_result.get("public_url")
                                       
            #         imagen_public_url = imagen_result.get("runway_url")
            #         results["generated_image"] = imagen_result
                    
            #         results["image_url"] = {
            #                     "public_url": imagen_public_url,
            #                     "runway_url": imagen_result.get("runway_url"),
            #                     "local_path": imagen_local_path
            #                                     }
                    
            #         logger.info(f"Imagen generada correctamente: {imagen_public_url}")
            #     except Exception as e:
            #         logger.error(f"Error generando imagen con ImageGenerator: {e}")
            # else:
            #     logger.warning("No se encontró texto para generar imagen (prompt_imagen es None).")
            
            imagen_public_url="https://pagina-de-presentacion3.onrender.com/images/8af7914d-7573-4f34-a90b-a8514407ba5c.jpg"
           
            # ===================== VIDEO =====================
            # if "tiktok" in data and "response" in data["tiktok"]:
            #     prompt_video = data["tiktok"]["response"]

            # if prompt_video:
            #     try:
            #         # ESTE ES EL PUNTO CLAVE:
            #         # generate_video retorna:
            #         # {
            #         #   "runway_url": runway_url,
            #         #   "public_url": public_url,
            #         #   "local_path": local_path,
            #         # }
            #         video_result = self.video_generator.generate_video(
            #             prompt_text=prompt_video
            #         )
            #         video_local_path = video_result.get("local_path")  # <- usamos el path local
            #         results["generated_video"] = video_result
                    
            #         results["video_url"] = {
            #         "public_url": video_result.get("public_url"),
            #         "runway_url": video_result.get("runway_url"),
            #         "local_path": video_local_path
            #     }
            #         logger.info(f"Video generado correctamente en: {video_local_path}")
            #     except Exception as e:
            #         logger.error(f"Error generando video con VideoGenerator: {e}")
            # else:
            #     logger.warning("No se encontró texto para generar video (prompt_video es None).")


            # # WhatsApp
            # # if "whatsapp" in data and "response" in data["whatsapp"]:
            # #     message = data["whatsapp"]["response"]
            # #     message=self.whatsapp.send_message(message_body=message,to_number="whatsapp:+59167769632")
                
            # #     results["whatsapp"] = message.sid
            # #     logger.info("enviado por whatsapp")
                
            # if "whatsapp" in data and "response" in data["whatsapp"]:
            #     message = data["whatsapp"]["response"]
            #     #response_whapi=self.whatsappwhapi.send_story_media(caption=message,media="https://mrmoviliano.com/wp-content/uploads/2020/01/jfif.jpg")
            #     response_whapi=self.whatsappwhapi.send_story_media(caption=message,media=imagen_public_url)
                
            #     results["whatsapp"] = response_whapi['message']['id']
            #     logger.info("enviado por whatsapp")


            # # # Facebook
            if "facebook" in data and "response" in data["facebook"]:
                message = data["facebook"]["response"]
                #results["facebook"] = self.facebook.publicar_texto(message)
                results["facebook"] = self.facebook.publicar_imagen(caption=message,image_url=imagen_public_url)


            # # # Instagram
            if "instagram" in data and "response" in data["instagram"]:
                message = data["instagram"]["response"]
                results["instagram"] = self.instagram.publicar(caption=message,image_url=imagen_public_url)

            # # # LinkedIn
            # if "linkedin" in data and "response" in data["linkedin"]:
            #     message = data["linkedin"]["response"]
            #     results["linkedin"] = self.linkedin.publicar(message)
          


            # TikTok
            
            # if "tiktok" in data and "response" in data["tiktok"]:
            #     message = data["tiktok"]["response"]
                
            #     #results["tiktok"] = self.tiktok.publicar_imagen_url_old_domain_very( texto=message,imagen_url="https://pagina-de-presentacion3.onrender.com/images/flores.jpg")
            #     #results["tiktok"] = self.tiktok.publicar_imagen_url( texto=message,imagen_url="https://mrmoviliano.com/wp-content/uploads/2020/01/jfif.jpg")
            #     if video_local_path:
            #         results["tiktok"] = self.tiktok.publicar(video_path=video_local_path)
            #     else:
            #         logger.info("No se generó video (video_local_path es None), no se publica en TikTok.")

            # logger.info("Mensajes enviados a todas las plataformas disponibles.")
            
            # results["urls"] = self.platform_urls
            
            return results

        except Exception as e:
            logger.error(f"Error en Sender.send: {e}")
            return {"error": str(e)}
