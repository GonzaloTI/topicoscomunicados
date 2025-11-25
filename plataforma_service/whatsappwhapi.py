# whatsappwhapi.py
import os
import logging
import requests
from flask import jsonify

logger = logging.getLogger(__name__)

class WhatsAppWhapi:
    def __init__(self):
        """Instancia el cliente de Whapi con las credenciales del entorno."""
        self.api_token = os.getenv('WHAPI_TOKEN')
        # Puedes definir la URL base en el entorno o dejarla fija si siempre usas la nube oficial
        self.base_url = os.getenv('WHAPI_API_URL', 'https://gate.whapi.cloud')

        if not self.api_token:
            raise ValueError("Falta la variable de entorno WHAPI_TOKEN.")

    def send_story(self, caption, background_color="#FF0B1E3B", font_type="COURIERPRIME_BOLD", contacts=None):
        """
        Envía un estado (Story) de texto a WhatsApp usando Whapi.
        
        Args:
            caption (str): El texto del estado.
            background_color (str): Color de fondo en Hex (8 dígitos). Default: Azul oscuro.
            font_type (str): Tipo de fuente. Default: COURIERPRIME_BOLD.
            contacts (list): Lista de IDs de contactos para mostrar el estado. Si es None o vacío, es público.
        """
        try:
            if not caption:
                return jsonify({'error': 'Falta el campo requerido: caption'}), 400

            endpoint = f"{self.base_url}/messages/story/text"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            # Preparamos el payload basado en tu cURL
            payload = {
                "contacts": contacts if contacts else [],
                "exclude_contacts": [], # Puedes agregar lógica para excluir si lo necesitas
                "caption": caption,
                "background_color": background_color,
                "caption_color": "#FFFFFFFF", # Blanco por defecto para que contraste
                "font_type": font_type
            }

            logger.info(f"Enviando Story a Whapi: {caption}")

            # Realizar la petición POST
            response = requests.post(endpoint, json=payload, headers=headers)

            # Verificar si la respuesta fue exitosa (Códigos 200-299)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Story enviada con éxito. ID: {data.get('sent', 'Unknown')}")

            return data

        except requests.exceptions.RequestException as e:
            # Captura errores específicos de la petición HTTP
            logger.error(f"Error de conexión con Whapi: {e}")
            # Intentamos obtener más detalles si el servidor respondió con error
            error_msg = str(e)
            if e.response is not None:
                try:
                    error_msg = e.response.json()
                except:
                    error_msg = e.response.text
            
            return jsonify({'error': error_msg}), 500

        except Exception as e:
            logger.error(f"Error general en send_story: {e}")
            return jsonify({'error': str(e)}), 500
        

    def send_story_media(self, media, caption="", contacts=None, exclude_contacts=None):
        """
        Envía un estado (Story) con IMAGEN/VIDEO a WhatsApp usando Whapi.

        Args:
            media (str): URL de la imagen/video o cadena base64 según soporte de Whapi.
            caption (str): Texto que acompaña a la imagen.
            contacts (list): Lista de contactos que verán el estado. [] = según privacidad general.
            exclude_contacts (list): Lista de contactos a excluir.
        """
        try:
            if not media:
                return jsonify({'error': 'Falta el campo requerido: media (URL o base64)'}), 400

            endpoint = f"{self.base_url}/stories/send/media"

            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            payload = {
                "media": media,
                "caption": caption or "",
                "contacts": contacts if contacts else [],
                "exclude_contacts": exclude_contacts if exclude_contacts else []
            }

            logger.info(f"Enviando Story MEDIA a Whapi. media={media} caption={caption}")

            response = requests.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            logger.info(f"Story (media) enviada con éxito. Respuesta: {data}")

            return data

        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión con Whapi (media): {e}")
            error_msg = str(e)
            if e.response is not None:
                try:
                    error_msg = e.response.json()
                except:
                    error_msg = e.response.text
            
            return jsonify({'error': error_msg}), 500

        except Exception as e:
            logger.error(f"Error general en send_story_media: {e}")
            return jsonify({'error': str(e)}), 500