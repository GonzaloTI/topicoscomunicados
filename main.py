from datetime import datetime
from email.utils import formataddr
import smtplib
import json, re
import time
import requests
from twilio.rest import Client
from flask import Flask, Response, json, jsonify, request, render_template
import psycopg2
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
import os
import logging
from openai import OpenAI
from openai import APIConnectionError, AuthenticationError, RateLimitError, APIStatusError
from flask import send_file, send_from_directory
from flask import redirect, g
import urllib.parse
import uuid
from functools import wraps
import jwt

from plataforma_service.whatsapp import WhatsApp
from sender import Sender
from sqlite import SQLiteUserDB

load_dotenv()

client_opneai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)


app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cambia-esta-clave-por-una-fuerte")

db = SQLiteUserDB()

TIKTOK_ACCESS_TOKEN = None
TIKTOK_REFRESH_TOKEN = None
TIKTOK_TOKEN_EXPIRES = None
TIKTOK_REFRESH_EXPIRES = None

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

# Carpeta donde se guardan las imágenes
IMAGES_FOLDER = os.path.join(os.getcwd(), "images")
os.makedirs(IMAGES_FOLDER, exist_ok=True)
VIDEO_FOLDER = os.path.join(os.getcwd(), "videos")
os.makedirs(VIDEO_FOLDER, exist_ok=True)


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
       
     
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({
                "error": "Token requerido. Usa el header Authorization: Bearer <token>"
            }), 401

        token = auth_header.split(" ", 1)[1]

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            # Guardamos el usuario autenticado en `g`
            g.current_user = {
                "user": data["user"],
                "cliente_id": data["cliente_id"]
            }
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401

        return f(*args, **kwargs)
    return decorated
  

@app.route("/login", methods=["POST"])
def login():
    """
    Body esperado:
    {
        "username": "admin",
        "password": "admin123"
    }

    Respuesta:
    {
        "user": "admin",
        "cliente_id": "1",
        "token": "<jwt>"
    }
    """
    try:
        data = request.get_json(force=True)
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "username y password son obligatorios"}), 400

        # Buscar usuario en SQLite
        user = db.get_user(username)
        if not user:
            return jsonify({"error": "Credenciales inválidas"}), 401

        # Validar password
        if not db.validate_password(user["password"], password):
            return jsonify({"error": "Credenciales inválidas"}), 401

        # Payload del token
        payload = {
            "user": user["username"],
            "cliente_id": user["cliente_id"]
        }

        # Generar token JWT
        token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
        if isinstance(token, bytes):  # por compatibilidad con algunas versiones
            token = token.decode("utf-8")

        return jsonify({
            "user": user["username"],
            "cliente_id": user["cliente_id"],
            "token": token
        }), 200

    except Exception as e:
        logger.error(f"Error en /login: {e}")
        return jsonify({"error": str(e)}), 500


  
 
@app.route("/")
def chat_ui():
    """
    Front.
    """
    return render_template("chatpublicaciones.html")

@app.route("/login-ui")
def login_ui():
    return render_template("login.html")



@app.route('/chatpublicaciones2', methods=['POST'])
def chatpublicaciones2():

    data = request.json
    
    body = data.get("Body")
    print(f'Mensaje recibido : {body}')
    cliente= data.get('cliente_id')
    
    logger.info(f"idcliente: {cliente}")
    
    if not cliente:
            return jsonify({"error": "Falta el campo cliente_id"}), 400
    
    try:
        # Obtener datos del mensaje
        body = data.get("Body")
     
        logger.warning(f"Mensaje entrante: msg: {body}")
        
        if not body or not isinstance(body, str) or body.strip() == "":
            return jsonify({"error": "El mensaje (Body) es obligatorio y no puede estar vacío."}), 400
       
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
      
        return jsonify({ 
            "status": results, 
            "publicaciones": respuesta_ia
            }), 200
    
    except Exception as e:
        logger.error(f"Error en Chat : {e}")
        return jsonify({"error": str(e)}), 500
 
 
@app.route('/chatpublicaciones', methods=['POST'])
def chatpublicaciones():

    try:
        data = request.json
        if not data:
            raise Exception("El body del request está vacío.")

        body = data.get("Body")
        cliente = data.get("cliente_id")

        print(f"Mensaje recibido : {body}")
        logger.info(f"idcliente: {cliente}")

        # Validar cliente_id
        if not cliente:
            raise Exception("Falta el campo cliente_id.")

        # Validar texto Body
        if not body or not isinstance(body, str) or body.strip() == "":
            raise Exception("El mensaje (Body) es obligatorio y no puede estar vacío.")

        # Validar longitud
        MAX_LEN = 1200
        if len(body) > MAX_LEN:
            raise Exception(f"El mensaje es demasiado largo. Máximo permitido: {MAX_LEN} caracteres.")

        logger.warning(f"Mensaje entrante: msg: {body}")

        # Generar respuesta IA
        respuesta_ia = generate_response_ia(
            question=body,
            historial_texto="historial_texto"
        )

        # Validar respuesta IA
        if (
            not respuesta_ia 
            or not isinstance(respuesta_ia, dict)
            or len(respuesta_ia.keys()) == 0
        ):
            raise Exception("La respuesta de IA es vacía o inválida.")

        # Validar que existan las 5 plataformas
        required_keys = ["instagram", "tiktok", "whatsapp", "facebook", "linkedin"]
        for key in required_keys:
            if key not in respuesta_ia:
                raise Exception(f"Falta la plataforma: {key}")
            if "response" not in respuesta_ia[key]:
                raise Exception(f"La plataforma {key} no contiene 'response'")

        # Enviar publicación
        results = Sender_service.send(respuesta_ia)
        #results = ""
        return jsonify({
            "status": results,
            "publicaciones": respuesta_ia
        }), 200

    except Exception as e:
        logger.error(f"Error en Chat : {e}")
        return jsonify({"error": str(e)}), 400

 
 
def generate_response_ia222(question, historial_texto):
    
    try:
        system_prompt = """
        Eres un asistente inteligente para la Facultad de Ciencias de la Computación que ayuda a crear publicaciones para redes sociales.

        **TU TAREA:**
        1. Analizar la intención del usuario
        2. Determinar si solicita crear publicaciones o es conversación general
        3. Responder en un formato JSON específico

        **TIPOS DE INTERACCIÓN:**

        A) **CONVERSACIÓN GENERAL** (saludos, preguntas, consultas):
        - Ejemplos: "hola", "buenos días", "¿qué puedes hacer?", "ayuda", "gracias"
        - Responde de forma amigable y explica tus capacidades

        B) **SOLICITUD DE PUBLICACIÓN**:
        - Ejemplos: "crea una publicación sobre...", "necesito post para...", "genera contenido sobre..."
        - Crea contenido adaptado para cada plataforma

        **FORMATO DE RESPUESTA (CRÍTICO - SOLO RETORNA ESTE JSON):**

        Para CONVERSACIÓN GENERAL:
        {
            "status": "conversacion",
            "mensaje": "Tu respuesta amigable aquí",
            "haypublicacion": false,
            "publicaciones": {}
        }

        Para SOLICITUD DE PUBLICACIÓN:
        {
            "status": "publicacion",
            "mensaje": "He creado publicaciones personalizadas para cada plataforma. ¿Te gustaría modificar alguna?",
            "haypublicacion": true,
            "publicaciones": {
                "facebook": {
                    "response": "Texto optimizado para Facebook (más extenso, incluye enlaces)"
                },
                "instagram": {
                    "response": "Texto para Instagram (incluye emojis y hashtags relevantes)"
                },
                "linkedin": {
                    "response": "Texto profesional para LinkedIn (tono formal, enfoque académico/profesional)"
                },
                "tiktok": {
                    "response": "Texto corto y dinámico para TikTok (muy visual, hashtags trending)"
                },
                "whatsapp": {
                    "response": "Texto directo para WhatsApp (conversacional, call-to-action claro)"
                }
            }
        }

        **REGLAS IMPORTANTES:**
        - Adapta el tono y longitud según cada plataforma
        - Instagram/TikTok: casual, emojis, hashtags
        - LinkedIn: profesional, educativo
        - Facebook: equilibrado, puede ser más largo
        - WhatsApp: directo, conversacional
        - SOLO retorna el JSON, sin texto adicional antes o después
        - Si no hay contexto suficiente, pregunta amablemente en el campo "mensaje"
        """
                
        user_prompt = f"""
        Mensaje del usuario: "{question}"

        Historial reciente: {historial_texto}

        Analiza la intención y responde en el formato JSON correspondiente.
        """

        # Llamada a OpenAI
        response = client_opneai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=1000
        )

        respuesta_texto = response.choices[0].message.content
        logger.info(f"Respuesta raw de IA: {respuesta_texto}")
        
        parsed = parse_json_relajado(respuesta_texto)
        
        # Validar estructura de respuesta
        if not parsed:
            logger.warning("No se pudo parsear la respuesta de IA")
            return {
                "status": "error",
                "mensaje": "Lo siento, ocurrió un error al procesar tu solicitud. Por favor, intenta de nuevo.",
                "haypublicacion": False,
                "publicaciones": {}
            }
        
        # Asegurar que tenga los campos requeridos
        if "status" not in parsed:
            parsed["status"] = "conversacion"
        if "mensaje" not in parsed:
            parsed["mensaje"] = "¿En qué puedo ayudarte?"
        if "haypublicacion" not in parsed:
            parsed["haypublicacion"] = False
        if "publicaciones" not in parsed:
            parsed["publicaciones"] = {}
        
        logger.info(f"Respuesta estructurada: {json.dumps(parsed, indent=2)}")
        return parsed

    except Exception as e:
        logger.error(f"Error en generate_response_ia: {e}")
        return {
            "status": "error",
            "mensaje": "Lo siento, ocurrió un error al generar la respuesta. Por favor, intenta de nuevo.",
            "haypublicacion": False,
            "publicaciones": {}
        }

 
 
 
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


##tiktok##########################################################################################

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGES_FOLDER, filename)

@app.route('/videos/<filename>')
def serve_videos(filename):
    return send_from_directory(VIDEO_FOLDER, filename)



@app.route("/upload_image", methods=["POST"])
def upload_image():
    """
    Recibe una imagen por form-data, la guarda en /images
    y devuelve la URL pública.
    """
    if "file" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Archivo vacío"}), 400

    # Extensión
    extension = os.path.splitext(file.filename)[1]
    if extension == "":
        extension = ".jpg"

    # Crear nombre único
    filename = f"{uuid.uuid4()}{extension}"

    # Ruta donde se guardará
    filepath = os.path.join(IMAGES_FOLDER, filename)

    # Guardar archivo
    file.save(filepath)

    # URL pública (ajusta tu dominio real verificado)
    public_url = f"https://pagina-de-presentacion3.onrender.com/images/{filename}"

    return jsonify({
        "mensaje": "Imagen subida correctamente",
        "filename": filename,
        "url_publica": public_url
    }), 200


@app.route('/tiktok3GffClh4aVVeakNpIa63P2wyvUSSEoYY.txt', methods=['GET'])
def serve_tiktok_file():
    return send_file("tiktok3GffClh4aVVeakNpIa63P2wyvUSSEoYY.txt")


@app.route('/callback', methods=['GET'])
def tiktok_callback():
    code = request.args.get("code")

    if not code:
        return "<h2>No llegó el code de TikTok.</h2>"

    try:
        # Mostrar toda la query como en Node.js
        query_data = json.dumps(request.args.to_dict(), indent=2)

        params = {
            "client_key": os.getenv("CLIENT_KEY"),
            "client_secret": os.getenv("CLIENT_SECRET"),
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": os.getenv("REDIRECT_URI")
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Petición a TikTok
        response = requests.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            data=params,
            headers=headers
        )

        response_json = response.json()
        response_data = json.dumps(response_json, indent=2)

        access_token = response_json.get("access_token", "")

        # ============================================================
        # GUARDAR TOKENS TEMPORALMENTE EN MEMORIA
        # ============================================================
        TIKTOK_ACCESS_TOKEN = response_json.get("access_token")
        TIKTOK_REFRESH_TOKEN = response_json.get("refresh_token")
        TIKTOK_TOKEN_EXPIRES = response_json.get("expires_in")
        TIKTOK_REFRESH_EXPIRES = response_json.get("refresh_expires_in")

        print("TOKENS GUARDADOS EN MEMORIA:")
        
        # HTML igual que en Node.js
        html = f"""
            <h2>Datos de la query recibida</h2>
            <pre>{query_data}</pre>

            <h2>Respuesta completa de TikTok</h2>
            <pre>{response_data}</pre>

            <h3>Subir video</h3>
            <form action="/uploadVideo" method="POST" enctype="multipart/form-data">
                <input type="hidden" name="access_token" value="{access_token}">
                <input type="file" name="video" accept="video/*">
                <button type="submit">Subir video a TikTok</button>
            </form>
        """

        return html

    except Exception as e:
        err = json.dumps(str(e), indent=2)
        return f"<h2>Error obteniendo token</h2><pre>{err}</pre>"


#####################login de tiktok###################
@app.route('/login_tiktok', methods=['GET'])
def tiktok_login():
    CLIENT_KEY = os.getenv("CLIENT_KEY")
    REDIRECT_URI = os.getenv("REDIRECT_URI")

    # Igual que encodeURIComponent
    redirect_uri_encoded = urllib.parse.quote(REDIRECT_URI, safe='')

    auth_url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={CLIENT_KEY}"
        f"&scope=video.upload,video.publish,user.info.basic"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri_encoded}"
    )

    return redirect(auth_url)
    
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
