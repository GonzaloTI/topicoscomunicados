# whatsapp.py
import os
import logging
from twilio.rest import Client
from flask import jsonify

logger = logging.getLogger(__name__)

class WhatsApp:
    def __init__(self):
        """Instancia el cliente de Twilio con las credenciales del entorno."""
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        sandbox_number = os.getenv('TWILIO_SANDBOX_NUMBER')

        if not account_sid or not auth_token or not sandbox_number:
            raise ValueError("Faltan variables de entorno de Twilio (SID, TOKEN o SANDBOX_NUMBER).")

        self.client = Client(account_sid, auth_token)
        self.from_number = f"whatsapp:{sandbox_number}"

    def send_message(self, to_number, message_body):
        """Envía un mensaje de WhatsApp usando Twilio."""
        try:
            if not to_number or not message_body:
                return jsonify({'error': 'Faltan campos requeridos: to y message'}), 400

            # Agregar prefijo whatsapp:
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'

            # Enviar mensaje
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_number
            )

            logger.info(f"Mensaje enviado a {to_number}: {message_body}")

            return  message

        except Exception as e:
            logger.error(f"Error en send_message: {e}")
            return jsonify({'error': str(e)}), 500
