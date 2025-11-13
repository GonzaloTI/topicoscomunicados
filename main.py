from datetime import datetime
from email.message import EmailMessage
from email.utils import formataddr
import smtplib
import json, re
import time
import requests
from twilio.rest import Client
from flask import Flask, Response, json, jsonify, request
import psycopg2
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import os
import logging
from openai import OpenAI
from openai import APIConnectionError, AuthenticationError, RateLimitError, APIStatusError


from plataforma_service.whatsapp import WhatsApp
from sender import Sender

load_dotenv()

client_opneai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s [%(levelname)s] %(message)s',  
    handlers=[
        logging.FileHandler("app.log"),   
        logging.StreamHandler()          
    ]
)

logger = logging.getLogger(__name__)

whatsapp = WhatsApp()
Sender_service = Sender()


import json, re

def parse_json_relajado(txt: str) -> dict:
    """Convierte texto o JSON parcial en dict de Python."""
    if isinstance(txt, dict):
        return txt
    if not isinstance(txt, str):
        return {}

    txt = txt.strip()

    # Intento directo
    try:
        parsed = json.loads(txt)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Extraer primer bloque {...}
    match = re.search(r'\{.*\}', txt, re.DOTALL)
    if match:
        candidate = match.group(0)
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    return {}



def generate_response_ia(question,historial_texto):
    
    try:
        
        
        system_prompt = """
            Eres un asistente para generar publicaciones en:instagram, tiktok , whathsap, facebook,linkedin
            tu generas el texto que tendra la publicacion para cada una de las platafromas, debe ser con relacion a la facultad de Ciencias de la computacion, 
            
            Reglas:
            - Usa lenguaje simple, claro y amigable dependiendo de cada plataforma.
            - Mantén el contexto según el historial de conversación.
            - Si hay continuidad (por ejemplo: "y esas?", "cuánto cuestan?"), interpreta el contexto anterior.
            - Si el mensaje es genérico (ej: "hola", "buenas tardes"), responde cordialmente pero sin ofrecer productos.

            Solo responde si entiendes el contexto. Si no hay suficiente contexto, pide más información de forma cordial.
            
            
            muy importante de debes retornar solo en este formato json nada mas sin ninguna alabra extra solo el texto con el formato json :
            
            {
               instagram:{
                   response :" texto de la publicacion  "
                   },
               tiktok:{
                   response :" texto de la publicacion "
                   } ,
               whatsapp:{
                   response :" texto de la publicacion  "
                   },
               facebook:{
                   response :" texto de la publicacion "
               } 
               linkedin:{
                   response :" texto de la publicacion "
               } 
            }
            
            """
        
        user_prompt = f"""
            instrucciones del cliente para la publicacion:
            {question}
            """

        # Llamada a OpenAI
        response = client_opneai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                
            ],
                temperature=0.7, max_tokens=800
        )
        # Loguear objeto completo (estado, id, model, usage, etc.)
        print(response)

        respuesta_texto = response.choices[0].message.content
        parsed = parse_json_relajado(respuesta_texto)
        
        print(parsed)
        
        #logger.info(f"Respuesta IA generada: {respuesta_texto}")
        return parsed

    except Exception as e:
        logger.error(f"Error en generate_response_ia: {e}")
        return "Lo siento, ocurrió un error al generar la respuesta."
    finally:
        pass
        



@app.route('/chatpublicaciones', methods=['POST'])
def chatpublicaciones():

    data = request.json
    
    body = data.get("Body")
    print(f'Mensaje recibido : {body}')
    cliente= data.get('cliente_id')
    
    logger.info(f"idcliente: {cliente}")
    
    try:
        # Obtener datos del mensaje
        body = data.get("Body")
     
        logger.warning(f"Mensaje entrante: msg: {body}")
       
        respuesta_ia =generate_response_ia(
            
            question=body ,
            historial_texto= "historial_texto"
           
            )
            
       # aqui parsear el resultado de respuesta_ia , porque nos retornara : 
        if not respuesta_ia or respuesta_ia == "Lo siento, ocurrió un error al generar la respuesta.":
            logger.error("La respuesta de IA es vacía o inválida")
            return jsonify({"error": "La respuesta de IA es vacía o inválida"}), 500

        results = Sender_service.send(respuesta_ia)
        # print(respuesta_ia)
        # results=respuesta_ia
      
        return jsonify({"resultados del envio ": results}), 200
    
    except Exception as e:
        logger.error(f"Error en webhook: {e}")
        return jsonify({"error": str(e)}), 500
 
 
@app.route('/testjson', methods=['POST'])
def test_json():
    try:
        data = request.get_json(force=True)
        print("Datos recibidos:", data)
        return jsonify({"recibido": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route('/send_message', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        to_number = data.get('to')
        message_body = data.get('message')

        if not to_number or not message_body:
            return jsonify({'error': 'Faltan campos requeridos: to y message'}), 400
        
        # Agregar prefijo 'whatsapp:' 
        if not to_number.startswith('whatsapp:'):
            to_number = 'whatsapp:' + to_number
        
        
        message = whatsapp.send_message(message_body=message_body,to_number=to_number)

        logger.info(f"Mensaje enviado a {to_number}: {message_body}")

        return jsonify({'status': 'Mensaje enviado', 'sid': message.sid}), 200

    except Exception as e:
        logger.error(f"Error en /send_message: {e}")
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/publicarinstagram', methods=['POST'])
def publicar_instagram():
    """
    Publica una publicación en Instagram con caption y una imagen.
    Body JSON esperado:
    {
        "caption": "Texto de la publicación",
        "image_url": "URL de la imagen"
    }
    """
    try:
        data = request.get_json(force=True)
        caption = data.get("caption")
        image_url = data.get("image_url")

        if not caption or not image_url:
            return jsonify({"error": "Faltan campos requeridos: caption o image_url"}), 400

        access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")  # o tu token directo
        user_id = os.getenv("INSTAGRAM_USER_ID")  # o tu user id directo

        # 1️⃣ Crear el contenedor de media
        media_url = f"https://graph.instagram.com/{user_id}/media"
        payload = {
            "caption": caption,
            "image_url": image_url,
            "access_token": access_token
        }
        resp = requests.post(media_url, data=payload)
        resp_json = resp.json()

        if "id" not in resp_json:
            return jsonify({"error": "No se pudo crear el contenedor de media", "detalle": resp_json}), 500

        creation_id = resp_json["id"]

        # 2️⃣ Publicar la media
        publish_url = f"https://graph.instagram.com/{user_id}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": access_token
        }
        publish_resp = requests.post(publish_url, data=publish_payload)
        publish_json = publish_resp.json()

        if "id" not in publish_json:
            return jsonify({"error": "No se pudo publicar la media", "detalle": publish_json}), 500

        # Retornar id de la publicación
        return jsonify({"publicacion_id": publish_json["id"], "creation_id": creation_id}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/publicarinstagram_reintento', methods=['POST'])
def publicarinstagram_reintento():
    """
    Publica una publicación en Instagram con caption y una imagen.
    Body JSON esperado:
    {
        "caption": "Texto de la publicación",
        "image_url": "URL de la imagen"
    }
    """
    try:
        data = request.get_json(force=True)
        caption = data.get("caption")
        image_url = data.get("image_url")

        if not caption or not image_url:
            logger.warning("Faltan campos requeridos: caption o image_url")
            return jsonify({"error": "Faltan campos requeridos: caption o image_url"}), 400

        access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        user_id = os.getenv("INSTAGRAM_USER_ID")

        # 1️⃣ Crear el contenedor de media
        media_url = f"https://graph.instagram.com/{user_id}/media"
        payload = {
            "caption": caption,
            "image_url": image_url,
            "access_token": access_token
        }
        resp = requests.post(media_url, data=payload)
        resp_json = resp.json()

        if "id" not in resp_json:
            logger.error(f"No se pudo crear el contenedor de media: {resp_json}")
            return jsonify({"error": "No se pudo crear el contenedor de media", "detalle": resp_json}), 500

        creation_id = resp_json["id"]
        logger.info(f"Contenedor de media creado: {creation_id}")

        # 2️⃣ Intentar publicar la media con reintentos
        publish_url = f"https://graph.instagram.com/{user_id}/media_publish"
        max_intentos = 5
        for intento in range(max_intentos):
            logger.info(f"Intento {intento} de publicar la media...")
            time.sleep(4)  # esperar 4 segundos entre intentos
            publish_payload = {
                "creation_id": creation_id,
                "access_token": access_token
            }
            publish_resp = requests.post(publish_url, data=publish_payload)
            publish_json = publish_resp.json()

            if "id" in publish_json:
                # Publicación exitosa
                logger.info(f"Publicación exitosa en intento {intento}")
                return jsonify({"publicacion_id": publish_json["id"], "creation_id": creation_id}), 200
            else:
                # Si es el último intento, devolver error
                logger.error(f"No se pudo publicar después de {max_intentos} intentos")
                if intento == max_intentos - 1:
                    return jsonify({"error": "No se pudo publicar la media después de varios intentos", "detalle": publish_json}), 500
                # Si no, seguir intentando
                continue

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/facebook/me', methods=['GET'])
def facebook_me_crudo():
    """
    Retorna el JSON crudo que entrega Facebook en /me
    """
    try:
        user_access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
        if not user_access_token:
            return jsonify({"error": "No se encontró FACEBOOK_PAGE_ACCESS_TOKEN"}), 400

        fb_url = "https://graph.facebook.com/v24.0/me"
        params = {"access_token": user_access_token}

        resp = requests.get(fb_url, params=params)
        return resp.text, resp.status_code, {'Content-Type': 'application/json'}

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/publicarfacebook', methods=['POST'])
def publicar_facebook():
    """
    Publica en una página de Facebook con texto y una imagen.
    Body JSON esperado:
    {
        "caption": "Texto de la publicación",
        "image_url": "URL de la imagen"
    }
    """
    try:
        data = request.get_json(force=True)
        caption = data.get("caption")
        image_url = data.get("image_url")

        if not caption or not image_url:
            return jsonify({"error": "Faltan campos requeridos: caption o image_url"}), 400

        page_id = os.getenv("FACEBOOK_PAGE_ID")  # o tu page id directo
        access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")  # token de página indefinido

        # 1️⃣ Publicar imagen + caption
        fb_url = f"https://graph.facebook.com/v24.0/{page_id}/photos"
        payload = {
            "url": image_url,
            "caption": caption,
            "access_token": access_token
        }
        resp = requests.post(fb_url, data=payload)
        resp_json = resp.json()

        if "id" not in resp_json:
            return jsonify({"error": "No se pudo publicar la imagen", "detalle": resp_json}), 500

        # Retornar id de la publicación
        return jsonify({"publicacion_id": resp_json["id"]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/publicarfacebook_texto', methods=['POST'])
def publicar_facebook_texto():
    """
    Publica solo texto en una página de Facebook.
    Body JSON esperado:
    {
        "message": "Texto de la publicación"
    }
    """
    try:
        data = request.get_json(force=True)
        message = data.get("message")

        if not message:
            return jsonify({"error": "Falta el campo requerido: message"}), 400

        page_id = os.getenv("FACEBOOK_PAGE_ID")  # o tu page id directo
        access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")  # token de página indefinido

        fb_url = f"https://graph.facebook.com/v24.0/{page_id}/feed"
        payload = {
            "message": message,
            "access_token": access_token
        }

        resp = requests.post(fb_url, data=payload)
        resp_json = resp.json()

        if "id" not in resp_json:
            return jsonify({"error": "No se pudo publicar el texto", "detalle": resp_json}), 500

        return jsonify({"publicacion_id": resp_json["id"]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



    
@app.route("/logs")
def get_logs():
    with open("app.log", "r") as f:
        content = f.read()
    return Response(content, mimetype="text/plain")

@app.route('/health/openai', methods=['GET'])
def health_openai():
    """
    GET /health/openai?model=gpt-3.5-turbo
    Verifica si la OPENAI_API_KEY funciona y si hay conectividad.
    Retorna JSON con ok, modelo, latencia y mensaje de error si falla.
    """
    model = request.args.get('model', 'gpt-3.5-turbo')
    api_key = os.getenv("OPENAI_API_KEY")
    key_present = bool(api_key)
    key_hint = (api_key[:4] + "..." + api_key[-4:]) if api_key and len(api_key) > 8 else None

    if not key_present:
        return jsonify({
            "ok": False,
            "status": "no_api_key",
            "message": "OPENAI_API_KEY no está definida en el entorno."
        }), 400

    t0 = time.time()
    try:
        # ping mínimo al modelo (1 token)
        resp = client_opneai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
            temperature=0
        )
        latency_ms = int((time.time() - t0) * 1000)
        return jsonify({
            "ok": True,
            "status": "up",
            "model": model,
            "latency_ms": latency_ms,
            "key_hint": key_hint,
            "reply": resp.choices[0].message.content.strip()
        }), 200

    except AuthenticationError as e:
        # 401 típico: API key inválida o sin permisos
        return jsonify({
            "ok": False,
            "status": "auth_error",
            "model": model,
            "key_hint": key_hint,
            "error": str(e)
        }), 401

    except (APIConnectionError,) as e:
        # Problema de red / DNS / TLS / firewall
        return jsonify({
            "ok": False,
            "status": "connection_error",
            "model": model,
            "key_hint": key_hint,
            "error": str(e)
        }), 502

    except (RateLimitError, APIStatusError) as e:
        # Límite / error de estado API
        return jsonify({
            "ok": False,
            "status": "api_error",
            "model": model,
            "key_hint": key_hint,
            "error": str(e)
        }), 503

    except Exception as e:
        # Cualquier otro caso
        return jsonify({
            "ok": False,
            "status": "unknown_error",
            "model": model,
            "key_hint": key_hint,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
